# Recidiviz - a data platform for criminal justice reform
# Copyright (C) 2020 Recidiviz, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# =============================================================================

"""Report context for the PO Monthly Report.

The PO Monthly Report is a report for parole and probation officers with feedback on measures they have taken to
improve individual outcomes. It aims to promote and increase the usage of measures such as early discharges, and
decrease the usage of measures such as revocations.

To generate a sample output for the PO Monthly Report email template, just run:

python -m recidiviz.reporting.context.po_monthly_report.context --state_code US_XX
"""
import argparse
import copy
import json
import sys
from datetime import date
from typing import Any, Dict, List, Literal, Optional

from jinja2 import Template

import recidiviz.reporting.email_reporting_utils as utils
from recidiviz.common.constants.state.state_supervision_period import (
    StateSupervisionLevel,
)
from recidiviz.common.constants.states import StateCode
from recidiviz.reporting.context.context_utils import (
    align_columns,
    format_date,
    format_full_name,
    format_given_name,
    format_greeting,
    format_violation_type,
    month_number_to_name,
)
from recidiviz.reporting.context.po_monthly_report.constants import (
    ABSCONSIONS,
    ASSESSMENTS,
    CRIME_REVOCATIONS,
    DEFAULT_MESSAGE_BODY_KEY,
    EARNED_DISCHARGES,
    FACE_TO_FACE,
    POS_DISCHARGES,
    SUPERVISION_DOWNGRADES,
    TECHNICAL_REVOCATIONS,
    Batch,
    OfficerHighlightComparison,
    OfficerHighlightType,
    ReportType,
)
from recidiviz.reporting.context.po_monthly_report.state_utils.po_monthly_report_metrics_delegate_factory import (
    PoMonthlyReportMetricsDelegateFactory,
)
from recidiviz.reporting.context.po_monthly_report.types import (
    AdverseOutcomeContext,
    ComplianceTaskContext,
    DecarceralMetricContext,
    OfficerHighlight,
    OfficerHighlightMetrics,
    OfficerHighlightMetricsComparison,
)
from recidiviz.reporting.context.report_context import ReportContext
from recidiviz.reporting.recipient import Recipient
from recidiviz.utils.environment import GCP_PROJECT_STAGING
from recidiviz.utils.metadata import local_project_id_override
from recidiviz.utils.string import StrictStringFormatter

_METRIC_DISPLAY_TEXT = {
    POS_DISCHARGES: "successful completions",
    EARNED_DISCHARGES: "early discharges",
    SUPERVISION_DOWNGRADES: "supervision downgrades",
    TECHNICAL_REVOCATIONS: "technical revocations",
    CRIME_REVOCATIONS: "new crime revocations",
    ABSCONSIONS: "absconsions",
    f"{TECHNICAL_REVOCATIONS}_zero_streak": "technical revocations",
    f"{CRIME_REVOCATIONS}_zero_streak": "new crime revocations",
    f"{ABSCONSIONS}_zero_streak": "absconsions",
}

_UPCOMING_LIST_LIMIT = 3
_OUT_OF_DATE_LIST_LIMIT = 4


def _client_full_name(client: Dict[str, Any]) -> str:
    # TODO(#10073) revert to bracket access once names are fully ingested
    return format_full_name(client.get("full_name", "{}"))


class PoMonthlyReportContext(ReportContext):
    """Report context for the PO Monthly Report."""

    def __init__(self, batch: Batch, recipient: Recipient):
        self.metrics_delegate = PoMonthlyReportMetricsDelegateFactory.build(
            state_code=batch.state_code
        )
        super().__init__(batch, recipient)
        self.recipient_data = self._prepare_recipient_data(recipient.data)

        self.state_name = self.state_code.get_state().name

    @property
    def attachment_template(self) -> Template:
        return self.jinja_env.get_template("po_monthly_report/attachment.txt.jinja2")

    def get_required_recipient_data_fields(self) -> List[str]:
        return self.metrics_delegate.required_recipient_data_fields

    def get_report_type(self) -> ReportType:
        return ReportType.POMonthlyReport

    @property
    def html_template(self) -> Template:
        return self.jinja_env.get_template("po_monthly_report/email.html.jinja2")

    def _prepare_recipient_data(self, data: dict) -> dict:
        recipient_data = copy.deepcopy(data)
        for int_key in [
            *self.metrics_delegate.decarceral_actions_metrics,
            *self.metrics_delegate.client_outcome_metrics,
            *self.metrics_delegate.total_metrics_for_display,
            *self.metrics_delegate.max_metrics_for_display,
            *self.metrics_delegate.zero_streak_metrics,
            *self.metrics_delegate.caseload_fields,
            *self.metrics_delegate.compliance_action_metrics,
        ]:
            recipient_data[int_key] = int(recipient_data[int_key])

        for float_key in [
            *self.metrics_delegate.average_metrics_for_display,
        ]:
            recipient_data[float_key] = float(recipient_data[float_key])

        return recipient_data

    def _prepare_for_generation(self) -> dict:
        """Executes PO Monthly Report data preparation."""
        self.prepared_data = {
            k: v
            for k, v in copy.deepcopy(self.recipient_data).items()
            if k in [utils.KEY_STATE_CODE]
        }

        self.prepared_data["static_image_path"] = utils.get_static_image_path(
            self.get_report_type()
        )

        self.prepared_data["greeting"] = format_greeting(
            self.recipient_data["officer_given_name"]
        )
        self.prepared_data["learn_more_link"] = self.properties["learn_more_link"]

        self.prepared_data["message_body"] = self._get_message_body()

        self.prepared_data["headline"] = f"Your {self._get_month_name()} Report"

        self.prepared_data["decarceral_outcomes"] = {
            metric: getattr(self, f"_get_{metric}")()
            for metric in self.metrics_delegate.decarceral_actions_metrics
        }

        self.prepared_data["adverse_outcomes"] = {
            metric: self._get_adverse_outcome(metric)
            for metric in self.metrics_delegate.client_outcome_metrics
        }

        self.prepared_data["compliance_tasks"] = {
            metric: self._get_compliance_context(metric)
            for metric in self.metrics_delegate.compliance_action_metrics
        }

        self.prepared_data["faq"] = self._get_faq()

        self.prepared_data["attachment_content"] = self._prepare_attachment_content()

        self.prepared_data[
            "show_case_triage_link"
        ] = self.metrics_delegate.has_case_triage

        return self.prepared_data

    def _prepare_attachment_content(self) -> Optional[str]:
        if not self._should_generate_attachment():
            return None

        return self.attachment_template.render(self._prepare_attachment_data())

    def _metric_improved(
        self, metric_key: str, metric_value: float, comparison_value: float
    ) -> bool:
        """Returns True if the value improved when compared to the comparison_value"""
        change_value = metric_value - comparison_value
        if metric_key in self.metrics_delegate.metrics_improve_on_increase:
            return change_value > 0
        return change_value < 0

    def _improved_over_state_average(self, metric_key: str) -> bool:
        return self._metric_improved(
            metric_key,
            self.recipient_data[metric_key],
            self.recipient_data[f"{metric_key}_state_average"],
        )

    def _improved_over_district_average(self, metric_key: str) -> bool:
        return self._metric_improved(
            metric_key,
            self.recipient_data[metric_key],
            self.recipient_data[f"{metric_key}_district_average"],
        )

    def _get_metrics_outperformed_region_averages(self) -> List[str]:
        """Returns a list of metrics that performed better than the either district or state averages"""
        return [
            metric_key
            for metric_key in self.metrics_delegate.decarceral_actions_metrics
            if self._improved_over_district_average(metric_key)
            or self._improved_over_state_average(metric_key)
        ]

    def _get_month_name(self) -> str:
        """Converts the number at the given key, representing a calendar month, into the name of that month."""
        return month_number_to_name(self.recipient_data["review_month"])

    def _get_compliance_context(self, metric: str) -> ComplianceTaskContext:
        """Examines data to determine whether compliance goal prompts should be active
        and sets data properties accordingly."""

        if metric == ASSESSMENTS:
            metric_label = "assessment"
        elif metric == FACE_TO_FACE:
            metric_label = "contact"
        else:
            raise ValueError(f"Unsupported metric type: {metric}")

        threshold = self.metrics_delegate.compliance_action_metric_goal_thresholds[
            metric
        ]
        caseload_count = self.recipient_data["caseload_count"]

        overdue_client_list = self.recipient_data[f"{metric}_out_of_date_clients"]
        overdue_count = len(overdue_client_list)

        compliant_count = caseload_count - overdue_count

        compliance_pct = 100 * compliant_count / caseload_count

        goal_count = min(
            overdue_count, self.metrics_delegate.max_compliance_goals[metric]
        )

        goal_pct = 100 * (compliant_count + goal_count) / caseload_count

        show_goal = compliance_pct < threshold
        goal_met = not show_goal

        upcoming_client_list = self.recipient_data[f"{metric}_upcoming_clients"]
        upcoming_clients = (
            [
                [
                    f'{_client_full_name(client)} ({client["person_external_id"]})',
                    StrictStringFormatter().format(
                        "{d:%B} {d.day}",
                        d=date.fromisoformat(client["recommended_date"]),
                    ),
                ]
                for client in upcoming_client_list[:_UPCOMING_LIST_LIMIT]
            ]
            if not self.metrics_delegate.has_case_triage
            else None
        )
        upcoming_overflow_text = (
            f"{len(upcoming_client_list) - _UPCOMING_LIST_LIMIT} more in attachment"
            if len(upcoming_client_list) > _UPCOMING_LIST_LIMIT
            else None
        )

        overdue_clients = (
            [
                [
                    f'{_client_full_name(client)} ({client["person_external_id"]})',
                ]
                for client in overdue_client_list[:_OUT_OF_DATE_LIST_LIMIT]
            ]
            if not self.metrics_delegate.has_case_triage
            else None
        )
        overdue_overflow_text = (
            f"{len(overdue_client_list) - _OUT_OF_DATE_LIST_LIMIT} more in attachment"
            if len(overdue_client_list) > _OUT_OF_DATE_LIST_LIMIT
            else None
        )

        return {
            "num_completed": self.recipient_data[metric],
            "pct": compliance_pct,
            "goal": goal_count,
            "goal_pct": goal_pct,
            "goal_met": goal_met,
            "show_goal": show_goal,
            "metric_label": metric_label,
            "metric": metric,
            "upcoming_clients": upcoming_clients,
            "upcoming_overflow_text": upcoming_overflow_text,
            "overdue_clients": overdue_clients,
            "overdue_overflow_text": overdue_overflow_text,
        }

    def _should_generate_attachment_section(self, clients_key: str) -> bool:
        return clients_key in self.recipient_data and self.recipient_data[clients_key]

    def _should_generate_attachment(self) -> bool:
        return any(
            self._should_generate_attachment_section(clients_key)
            for clients_key in self.metrics_delegate.client_fields
        )

    def _prepare_attachment_clients_tables(self) -> Dict[str, List[List[str]]]:
        """
        Prepares "tables" (2 dimensional arrays) of client details to inline into the email
        Returns: a dictionary, keyed by client "type", and its corresponding table
        """
        clients_by_type: Dict[str, List[List[str]]] = {}

        for clients_key in self.metrics_delegate.client_fields:
            clients_by_type[clients_key] = []

            if not self._should_generate_attachment_section(clients_key):
                continue

            for client in self.recipient_data[clients_key]:
                base_columns = [
                    f"[{client['person_external_id']}]",
                    # TODO(#7374): Revert to bracket access when current investigation
                    # is figured out.
                    client.get("full_name", "{}"),
                ]
                additional_columns = []

                if clients_key == "pos_discharges_clients":
                    additional_columns = [
                        f'Supervision completed on {format_date(client["successful_completion_date"])}'
                    ]
                elif clients_key == "earned_discharges_clients":
                    additional_columns = [
                        f'Discharge granted on {format_date(client["earned_discharge_date"])}'
                    ]
                elif clients_key == "supervision_downgrades_clients":
                    additional_columns = [
                        f'Supervision level downgraded on {format_date(client["latest_supervision_downgrade_date"])}'
                    ]
                elif clients_key == "absconsions_clients":
                    additional_columns = [
                        f'Absconsion reported on {format_date(client["absconsion_report_date"])}'
                    ]
                elif clients_key == "revocations_clients":
                    additional_columns = [
                        f'{format_violation_type(client["revocation_violation_type"])}',
                        f'Revocation recommendation staffed on {format_date(client["revocation_report_date"])}',
                    ]
                elif clients_key == "assessments_upcoming_clients":
                    additional_columns = [
                        f'Due on {format_date(client["recommended_date"])}'
                    ]
                elif clients_key == "facetoface_upcoming_clients":
                    additional_columns = [
                        f'Recommended on {format_date(client["recommended_date"])}'
                    ]

                clients_by_type[clients_key].append(base_columns + additional_columns)

        for clients in clients_by_type.values():
            clients.sort(key=lambda x: json.loads(x[1]).get("surname", ""))
            for client in clients:
                client[1] = format_full_name(client[1], last_name_first=True)
        return clients_by_type

    def _prepare_attachment_data(self) -> Dict:
        prepared_on_date = format_date(
            self.get_batch_id(), current_format="%Y%m%d%H%M%S"
        )

        return {
            "prepared_on_date": prepared_on_date,
            "officer_given_name": format_given_name(
                self.recipient_data["officer_given_name"]
            ),
            "clients": {
                clients_key: align_columns(clients)
                for clients_key, clients in self._prepare_attachment_clients_tables().items()
            },
        }

    def _caseload_or_district_outcome_text(self, metric: str) -> Optional[str]:
        district_total = int(self.recipient_data[f"{metric}_district_total"])
        recipient_total = int(self.recipient_data[metric])

        if recipient_total:
            return f"{recipient_total:n} from your caseload"

        if district_total:
            return f"{district_total:n} from your district"

        return None

    def _get_pos_discharges(self) -> DecarceralMetricContext:
        """Creates context data for the Successful Completions card"""
        state_total = int(self.recipient_data[f"{POS_DISCHARGES}_state_total"])
        main_text = (
            f"{{}} people completed supervision in {self.state_name} last month."
        )

        supplemental_text = self._caseload_or_district_outcome_text(POS_DISCHARGES)

        action_text = f"Clients who have their {self.metrics_delegate.completion_date_label} this month"

        action_clients = self.recipient_data["upcoming_release_date_clients"]

        action_table = (
            [
                [
                    f'{_client_full_name(client)} ({client["person_external_id"]})',
                    StrictStringFormatter().format(
                        "{d:%B} {d.day}",
                        d=date.fromisoformat(client["projected_end_date"]),
                    ),
                ]
                for client in action_clients
            ]
            if len(action_clients)
            else None
        )

        return {
            "heading": "Successful Completions",
            "icon": "ic_case-completions-v2.png",
            "main_text": main_text,
            "total": state_total,
            "supplemental_text": supplemental_text,
            "action_text": action_text,
            "action_table": action_table,
        }

    def _get_earned_discharges(self) -> DecarceralMetricContext:
        """Creates context data for the Early Releases card"""
        state_total = int(self.recipient_data[f"{EARNED_DISCHARGES}_state_total"])
        main_text = f"{{}} early discharge requests filed across {self.state_name}."

        supplemental_text = self._caseload_or_district_outcome_text(EARNED_DISCHARGES)

        return {
            "heading": "Early Discharges",
            "icon": "ic_early-discharges-v2.png",
            "main_text": main_text,
            "total": state_total,
            "supplemental_text": supplemental_text,
            "action_text": None,
            "action_table": None,
        }

    def _get_supervision_downgrades(self) -> DecarceralMetricContext:
        """Creates context data for the Successful Completions card"""
        state_total = int(self.recipient_data[f"{SUPERVISION_DOWNGRADES}_state_total"])

        main_text = "{} clients had their supervision downgraded last month."

        supplemental_text = self._caseload_or_district_outcome_text(
            SUPERVISION_DOWNGRADES
        )

        action_text = "Clients who may be downgraded based on their last assessment"

        action_clients = self.recipient_data["mismatches"]

        action_table = (
            [
                [
                    f'{_client_full_name(client)} ({client["person_external_id"]})',
                    f"{self.metrics_delegate.get_supervision_level_label(client['current_supervision_level'])} &rarr; {self.metrics_delegate.get_supervision_level_label(client['recommended_level'])}",
                ]
                for client in action_clients
            ]
            if len(action_clients)
            else None
        )

        return {
            "heading": "Supervision Downgrades",
            "icon": "ic_supervision-downgrades-v2.png",
            "main_text": main_text,
            "total": state_total,
            "supplemental_text": supplemental_text,
            "action_text": action_text,
            "action_table": action_table,
        }

    def _get_adverse_outcome(self, data_key: str) -> AdverseOutcomeContext:
        label = _METRIC_DISPLAY_TEXT[data_key].title()
        count = int(self.recipient_data[data_key])

        outcome_context: AdverseOutcomeContext = {
            "label": label,
            "count": count,
        }

        zero_streak = int(self.recipient_data[f"{data_key}_zero_streak"])
        if zero_streak > 1:
            outcome_context["zero_streak"] = zero_streak
        else:
            district_average = float(
                self.recipient_data[f"{data_key}_district_average"]
            )
            diff = count - district_average
            if diff >= 1:
                outcome_context["amount_above_average"] = diff

        return outcome_context

    def _get_message_body(self) -> str:
        """Constructs message body string with optional highlight text."""

        if message_override := self.recipient_data.get("message_body_override"):
            return message_override

        highlight_text = ""

        highlight: Optional[OfficerHighlight] = None
        for highlight_fn in [
            self._get_most_decarceral_highlight,
            self._get_longest_zero_streak_highlight,
            self._get_above_average_highlight,
        ]:
            highlight = highlight_fn()
            if highlight is not None:
                break

        if highlight is not None:
            metrics = [_METRIC_DISPLAY_TEXT[m] for m in highlight["metrics"]]
            if len(metrics) > 1:
                serial_comma = "," if len(metrics) > 2 else ""
                metrics_text = (
                    ", ".join(metrics[:-1]) + f"{serial_comma} and {metrics[-1]}"
                )
            else:
                metrics_text = metrics[0]

            if highlight["type"] == OfficerHighlightType.ABOVE_AVERAGE_DECARCERAL:
                highlight_text = (
                    f"Last month, you had more {metrics_text} than officers like you. "
                    "Keep up the great work! "
                )
            else:
                comparison = highlight["compared_to"]

                if comparison == OfficerHighlightComparison.STATE:
                    comparison_text = self.state_name
                elif comparison == OfficerHighlightComparison.DISTRICT:
                    comparison_text = "your district"

                if highlight["type"] == OfficerHighlightType.MOST_DECARCERAL:
                    highlight_text = (
                        f"Last month, you had the most {metrics_text} "
                        f"out of anyone in {comparison_text}. Amazing work! "
                    )

                if (
                    highlight["type"]
                    == OfficerHighlightType.LONGEST_ADVERSE_ZERO_STREAK
                ):
                    # if there is more than one they should be the same; just use the first
                    streak_length = self.recipient_data[highlight["metrics"][0]]
                    if highlight["compared_to"] == OfficerHighlightComparison.SELF:
                        exhortation = "Keep it up!"
                    else:
                        exhortation = (
                            f"This is the most out of anyone in {comparison_text}. "
                            "Way to go!"
                        )
                    highlight_text = (
                        f"You have gone {streak_length} months without "
                        f"having any {metrics_text}. {exhortation} "
                    )

        return f"{highlight_text}{self.properties[DEFAULT_MESSAGE_BODY_KEY]}"

    def _get_max_comparison_highlight(
        self,
        metrics: List[str],
        highlight_type: Literal[
            OfficerHighlightType.MOST_DECARCERAL,
            OfficerHighlightType.LONGEST_ADVERSE_ZERO_STREAK,
        ],
        min_threshold: int = 0,
    ) -> Optional[OfficerHighlightMetricsComparison]:
        """Compares recipient metric to state and district maximum. Returns a highlight
        if recipient's value equals either maximum (state takes precedence),
        None otherwise."""
        state_highlights = [
            m
            for m in metrics
            if self.recipient_data[m] == self.recipient_data[f"{m}_state_max"]
            and self.recipient_data[m] > min_threshold
        ]
        if state_highlights:
            return {
                "type": highlight_type,
                "metrics": state_highlights,
                "compared_to": OfficerHighlightComparison.STATE,
            }

        district_highlights = [
            m
            for m in metrics
            if self.recipient_data[m] == self.recipient_data[f"{m}_district_max"]
            and self.recipient_data[m] > min_threshold
        ]
        if district_highlights:
            return {
                "type": highlight_type,
                "metrics": district_highlights,
                "compared_to": OfficerHighlightComparison.DISTRICT,
            }

        return None

    def _get_most_decarceral_highlight(
        self,
    ) -> Optional[OfficerHighlightMetricsComparison]:
        return self._get_max_comparison_highlight(
            self.metrics_delegate.decarceral_actions_metrics,
            OfficerHighlightType.MOST_DECARCERAL,
        )

    def _get_longest_zero_streak_highlight(
        self,
    ) -> Optional[OfficerHighlightMetricsComparison]:
        highlight = self._get_max_comparison_highlight(
            self.metrics_delegate.zero_streak_metrics,
            OfficerHighlightType.LONGEST_ADVERSE_ZERO_STREAK,
            min_threshold=1,
        )

        if highlight is None:
            zero_streaks = [
                self.recipient_data[m]
                for m in self.metrics_delegate.zero_streak_metrics
            ]
            personal_metrics = [
                m
                for m in self.metrics_delegate.zero_streak_metrics
                if self.recipient_data[m] > 1
                and self.recipient_data[m] == max(zero_streaks)
            ]
            if personal_metrics:
                highlight = {
                    "type": OfficerHighlightType.LONGEST_ADVERSE_ZERO_STREAK,
                    "metrics": personal_metrics,
                    "compared_to": OfficerHighlightComparison.SELF,
                }

        return highlight

    def _get_above_average_highlight(self) -> Optional[OfficerHighlightMetrics]:
        metrics = self._get_metrics_outperformed_region_averages()
        if metrics:
            return {
                "type": OfficerHighlightType.ABOVE_AVERAGE_DECARCERAL,
                "metrics": metrics,
            }
        return None

    def _get_faq(self) -> dict:
        return self.properties["faq"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--state_code", dest="state_code", type=StateCode, required=True
    )
    known_args, _ = parser.parse_known_args(sys.argv)

    demo_state_code = known_args.state_code

    if demo_state_code is None:
        raise ValueError("You must supply a valid state code.")

    context = PoMonthlyReportContext(
        Batch(
            state_code=demo_state_code,
            batch_id="20211029135032",
            report_type=ReportType.POMonthlyReport,
        ),
        Recipient.from_report_json(
            {
                utils.KEY_EMAIL_ADDRESS: "test@recidiviz.org",
                utils.KEY_STATE_CODE: demo_state_code.value,
                utils.KEY_DISTRICT: None,
                # the data source may provide values for fields we don't intend to use
                # for a given state; this fixture emulates that, including all fields
                # defined on the view. States should ignore them as needed
                "pos_discharges": 0,
                "earned_discharges": 0,
                "supervision_downgrades": 2,
                "technical_revocations": 0,
                "crime_revocations": 1,
                "absconsions": 2,
                "pos_discharges_district_average": 0,
                "pos_discharges_state_average": 0,
                "earned_discharges_district_average": 0,
                "earned_discharges_state_average": 0,
                "supervision_downgrades_district_average": 0,
                "supervision_downgrades_state_average": 0,
                "pos_discharges_district_total": 38,
                "pos_discharges_state_total": 273,
                "earned_discharges_district_total": 0,
                "earned_discharges_state_total": 163,
                "supervision_downgrades_district_total": 56,
                "supervision_downgrades_state_total": 391,
                "pos_discharges_district_max": 5,
                "pos_discharges_state_max": 5,
                "earned_discharges_district_max": 5,
                "earned_discharges_state_max": 5,
                "supervision_downgrades_district_max": 5,
                "supervision_downgrades_state_max": 5,
                "technical_revocations_district_average": 0,
                "technical_revocations_state_average": 0,
                "crime_revocations_district_average": 1.356,
                "crime_revocations_state_average": 0,
                "absconsions_district_average": 0.5743,
                "absconsions_state_average": 0,
                "pos_discharges_last_month": 0,
                "earned_discharges_last_month": 0,
                "supervision_downgrades_last_month": 0,
                "technical_revocations_last_month": 0,
                "crime_revocations_last_month": 0,
                "absconsions_last_month": 0,
                "technical_revocations_zero_streak": 5,
                "crime_revocations_zero_streak": 0,
                "absconsions_zero_streak": 0,
                "technical_revocations_zero_streak_state_max": 5,
                "technical_revocations_zero_streak_district_max": 5,
                "crime_revocations_zero_streak_state_max": 12,
                "crime_revocations_zero_streak_district_max": 12,
                "absconsions_zero_streak_state_max": 12,
                "absconsions_zero_streak_district_max": 12,
                "pos_discharges_clients": [],
                "earned_discharges_clients": [],
                "supervision_downgrades_clients": [],
                "absconsions_clients": [],
                "assessments_upcoming_clients": [
                    {
                        "person_external_id": "112",
                        "full_name": '{"given_names": "CONSUELO", "surname": "MEDINA"}',
                        "recommended_date": "2021-05-03",
                    },
                    {
                        "person_external_id": "121",
                        "full_name": '{"given_names": "SONYA", "surname": "BAUTISTA"}',
                        "recommended_date": "2021-05-07",
                    },
                    {
                        "person_external_id": "124",
                        "recommended_date": "2021-05-07",
                    },
                    {
                        "person_external_id": "117",
                        "full_name": '{"given_names": "MIRAN", "surname": "PENA"}',
                        "recommended_date": "2021-05-11",
                    },
                    {
                        "person_external_id": "138",
                        "full_name": '{"given_names": "PEPI", "surname": "BAKER"}',
                        "recommended_date": "2021-05-15",
                    },
                    {
                        "person_external_id": "137",
                        "full_name": '{"given_names": "FLORENCE", "surname": "GUTIERREZ"}',
                        "recommended_date": "2021-05-29",
                    },
                ],
                "assessments_out_of_date_clients": [
                    {
                        "person_external_id": "131",
                    },
                    {
                        "person_external_id": "123",
                        "full_name": '{"given_names": "LISSA", "surname": "MEZA"}',
                    },
                    {
                        "person_external_id": "116",
                        "full_name": '{"given_names": "DANIELE", "surname": "MORROW"}',
                    },
                ],
                "facetoface_upcoming_clients": [
                    {
                        "person_external_id": "120",
                        "full_name": '{"given_names": "MAGGEE", "surname": "FINLEY"}',
                        "recommended_date": "2021-05-05",
                    },
                    {
                        "person_external_id": "110",
                        "recommended_date": "2021-05-09",
                    },
                    {
                        "person_external_id": "122",
                        "full_name": '{"given_names": "EMILINE", "surname": "RICHMOND"}',
                        "recommended_date": "2021-05-19",
                    },
                ],
                "facetoface_out_of_date_clients": [
                    {
                        "person_external_id": "108",
                        "full_name": '{"given_names": "KORE", "surname": "CHURCH"}',
                    },
                    {
                        "person_external_id": "128",
                    },
                    {
                        "person_external_id": "106",
                        "full_name": '{"given_names": "SHEILAH", "surname": "MARTINEZ"}',
                    },
                    {
                        "person_external_id": "107",
                        "full_name": '{"given_names": "CLARIBEL", "surname": "VELAZQUEZ"}',
                    },
                    {
                        "person_external_id": "133",
                        "full_name": '{"given_names": "ALMETA", "surname": "OWENS"}',
                    },
                    {
                        "person_external_id": "118",
                        "full_name": '{"given_names": "CHERY", "surname": "CURRY"}',
                    },
                    {
                        "person_external_id": "119",
                        "full_name": '{"given_names": "FLORINA", "surname": "ASHLEY"}',
                    },
                    {
                        "person_external_id": "129",
                        "full_name": '{"given_names": "BERT", "surname": "MELTON"}',
                    },
                    {
                        "person_external_id": "132",
                        "full_name": '{"given_names": "MARCY", "surname": "HATFIELD"}',
                    },
                    {
                        "person_external_id": "115",
                        "full_name": '{"given_names": "GAYLE", "surname": "CONWAY"}',
                    },
                    {
                        "person_external_id": "139",
                        "full_name": '{"given_names": "GEORGEANNE", "surname": "MCFADDEN"}',
                    },
                    {
                        "person_external_id": "130",
                        "full_name": '{"given_names": "ISADORA", "surname": "DONOVAN"}',
                    },
                ],
                "revocations_clients": [],
                "upcoming_release_date_clients": [
                    {
                        "person_external_id": "105",
                        "projected_end_date": "2021-05-07",
                    },
                    {
                        "full_name": '{"given_names": "REBEKAH", "surname": "CORTES"}',
                        "person_external_id": "142",
                        "projected_end_date": "2021-05-18",
                    },
                ],
                "assessments": "7",
                "facetoface": "94",
                "caseload_count": "73",
                "officer_external_id": 0,
                "officer_given_name": "Clementine",
                "review_month": 4,
                "mismatches": [
                    {
                        "full_name": '{"given_names": "TONYE", "surname": "THOMPSON"}',
                        "person_external_id": "189472",
                        "current_supervision_level": StateSupervisionLevel.MEDIUM.value,
                        "recommended_level": StateSupervisionLevel.MINIMUM.value,
                    },
                    {
                        "full_name": '{"given_names": "LINET", "surname": "HANSEN"}',
                        "person_external_id": "47228",
                        "current_supervision_level": StateSupervisionLevel.MEDIUM.value,
                        "recommended_level": StateSupervisionLevel.MINIMUM.value,
                    },
                    {
                        "full_name": '{"given_names": "REBEKAH", "surname": "CORTES"}',
                        "person_external_id": "132878",
                        "current_supervision_level": StateSupervisionLevel.HIGH.value,
                        "recommended_level": StateSupervisionLevel.MEDIUM.value,
                    },
                    {
                        "person_external_id": "147872",
                        "current_supervision_level": StateSupervisionLevel.HIGH.value,
                        "recommended_level": StateSupervisionLevel.MINIMUM.value,
                    },
                ],
            }
        ),
    )

    with local_project_id_override(GCP_PROJECT_STAGING):
        prepared_data = context.get_prepared_data()
        prepared_data["static_image_path"] = "./recidiviz/reporting/context/static"

    print(context.html_template.render(**prepared_data))
