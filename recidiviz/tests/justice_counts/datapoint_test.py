# Recidiviz - a data platform for criminal justice reform
# Copyright (C) 2022 Recidiviz, Inc.
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
"""This class implements tests for the Justice Counts DatapointInterface."""


import datetime

from recidiviz.common.constants.justice_counts import ContextKey
from recidiviz.justice_counts.datapoint import DatapointInterface
from recidiviz.justice_counts.dimensions.law_enforcement import CallType
from recidiviz.justice_counts.exceptions import JusticeCountsServerError
from recidiviz.justice_counts.metrics import law_enforcement
from recidiviz.justice_counts.report import ReportInterface
from recidiviz.persistence.database.schema.justice_counts.schema import (
    Agency,
    Datapoint,
    Report,
    ReportingFrequency,
    ReportStatus,
    UserAccount,
)
from recidiviz.persistence.database.session_factory import SessionFactory
from recidiviz.tests.justice_counts.utils import (
    JusticeCountsDatabaseTestCase,
    JusticeCountsSchemaTestObjects,
)


class TestDatapointInterface(JusticeCountsDatabaseTestCase):
    """Implements tests for the UserAccountInterface."""

    def setUp(self) -> None:
        super().setUp()
        self.test_schema_objects = JusticeCountsSchemaTestObjects()

    def test_save_agency_datapoints_turnoff_whole_metric(self) -> None:
        with SessionFactory.using_database(self.database_key) as session:
            agency = self.test_schema_objects.test_agency_A
            session.add(agency)
            agency_metric = self.test_schema_objects.get_agency_metric_interface(
                is_metric_enabled=False
            )
            DatapointInterface.add_or_update_agency_datapoints(
                agency_metric=agency_metric, agency=agency, session=session
            )
            datapoints = session.query(Datapoint).all()
            self.assertEqual(len(datapoints), 1)
            self.assertEqual(datapoints[0].enabled, False)
            self.assertEqual(datapoints[0].metric_definition_key, agency_metric.key)
            self.assertEqual(datapoints[0].dimension_identifier_to_member, None)
            self.assertEqual(datapoints[0].context_key, None)

    def test_save_agency_datapoints_turnoff_disaggregation(self) -> None:
        with SessionFactory.using_database(self.database_key) as session:
            session.add(self.test_schema_objects.test_agency_A)
            agency = session.query(Agency).one()
            agency_metric = self.test_schema_objects.get_agency_metric_interface(
                include_disaggregation=True
            )
            DatapointInterface.add_or_update_agency_datapoints(
                agency_metric=agency_metric, agency=agency, session=session
            )
            datapoints = session.query(Datapoint).all()
            self.assertEqual(len(datapoints), len(CallType))
            datapoints.sort(
                key=lambda d: list(d.dimension_identifier_to_member.values())[0]
            )
            self.assertEqual(datapoints[0].enabled, False)
            self.assertEqual(
                datapoints[0].dimension_identifier_to_member,
                {CallType.dimension_identifier(): "EMERGENCY"},
            )
            self.assertEqual(datapoints[1].enabled, False)
            self.assertEqual(
                datapoints[1].dimension_identifier_to_member,
                {CallType.dimension_identifier(): "NON_EMERGENCY"},
            )
            self.assertEqual(
                datapoints[2].dimension_identifier_to_member,
                {CallType.dimension_identifier(): "UNKNOWN"},
            )
            self.assertEqual(datapoints[2].enabled, False)

    def test_save_agency_datapoints_disable_single_breakdown(self) -> None:
        with SessionFactory.using_database(self.database_key) as session:
            session.add(self.test_schema_objects.test_agency_A)
            agency = session.query(Agency).one()
            agency_metric = self.test_schema_objects.get_agency_metric_interface(
                use_partially_disabled_disaggregation=True, include_disaggregation=True
            )
            DatapointInterface.add_or_update_agency_datapoints(
                agency_metric=agency_metric, agency=agency, session=session
            )
            datapoints = session.query(Datapoint).all()
            self.assertEqual(len(datapoints), 2)
            self.assertEqual(datapoints[0].enabled, False)
            self.assertEqual(datapoints[1].enabled, False)
            self.assertEqual(
                datapoints[0].dimension_identifier_to_member,
                {CallType.dimension_identifier(): "NON_EMERGENCY"},
            )
            self.assertEqual(
                datapoints[1].dimension_identifier_to_member,
                {CallType.dimension_identifier(): "UNKNOWN"},
            )

    def test_save_agency_datapoints_reenable_breakdown(self) -> None:
        with SessionFactory.using_database(self.database_key) as session:
            session.add(self.test_schema_objects.test_agency_A)
            agency = session.query(Agency).one()
            agency_metric = self.test_schema_objects.get_agency_metric_interface(
                include_disaggregation=True
            )
            DatapointInterface.add_or_update_agency_datapoints(
                agency_metric=agency_metric, agency=agency, session=session
            )
            datapoints = session.query(Datapoint).all()
            self.assertEqual(len(datapoints), 3)
            # Reenable DETENTION disaggregation, this will delete the datapoint
            agency_metric = self.test_schema_objects.get_agency_metric_interface(
                use_partially_disabled_disaggregation=True, include_disaggregation=True
            )
            DatapointInterface.add_or_update_agency_datapoints(
                agency_metric=agency_metric, agency=agency, session=session
            )
            datapoints = session.query(Datapoint).all()
            self.assertEqual(len(datapoints), 2)

    def test_save_agency_datapoints_reenable_metric(self) -> None:
        with SessionFactory.using_database(self.database_key) as session:
            session.add(self.test_schema_objects.test_agency_A)
            agency = session.query(Agency).one()
            agency_metric = self.test_schema_objects.get_agency_metric_interface(
                is_metric_enabled=False
            )
            DatapointInterface.add_or_update_agency_datapoints(
                agency_metric=agency_metric, agency=agency, session=session
            )
            datapoints = session.query(Datapoint).all()
            self.assertEqual(len(datapoints), 1)
            agency_metric = self.test_schema_objects.get_agency_metric_interface(
                is_metric_enabled=True
            )
            DatapointInterface.add_or_update_agency_datapoints(
                agency_metric=agency_metric, agency=agency, session=session
            )
            datapoints = session.query(Datapoint).all()
            self.assertEqual(len(datapoints), 0)

    def test_save_agency_datapoints_contexts(self) -> None:
        with SessionFactory.using_database(self.database_key) as session:
            session.add(self.test_schema_objects.test_agency_A)
            agency = session.query(Agency).one()
            agency_metric = self.test_schema_objects.get_agency_metric_interface(
                include_contexts=True, include_disaggregation=True
            )
            DatapointInterface.add_or_update_agency_datapoints(
                agency_metric=agency_metric, agency=agency, session=session
            )
            datapoints = session.query(Datapoint).all()
            # One context datapoint, 3 disaggregation datapoints
            self.assertEqual(len(datapoints), 4)
            for datapoint in datapoints:
                if datapoint.context_key is None:
                    self.assertEqual(datapoint.enabled, False)
                else:
                    self.assertEqual(
                        datapoint.context_key, ContextKey.ADDITIONAL_CONTEXT.value
                    )
                    self.assertEqual(
                        datapoint.value, "this additional context provides contexts"
                    )

    def test_save_invalid_datapoint(self) -> None:
        with SessionFactory.using_database(self.database_key) as session:
            monthly_report = self.test_schema_objects.test_report_monthly
            user = self.test_schema_objects.test_user_A
            session.add_all([monthly_report, user])
            current_time = datetime.datetime.now(tz=datetime.timezone.utc)

            try:
                # When a report is in Draft mode, no errors are raised when the value is invalid
                DatapointInterface.add_datapoint(
                    session=session,
                    report=monthly_report,
                    value="123abc",
                    user_account=user,
                    metric_definition_key=law_enforcement.annual_budget.key,
                    current_time=current_time,
                )
                assert True
            except ValueError:
                assert False

            with self.assertRaises(JusticeCountsServerError):
                # When a report is Published, an errors is raised when the value is invalid
                monthly_report = session.query(Report).one()
                user = session.query(UserAccount).one()
                ReportInterface.update_report_metadata(
                    session=session,
                    report=monthly_report,
                    editor_id=user.id,
                    status=ReportStatus.PUBLISHED.value,
                )
                DatapointInterface.add_datapoint(
                    session=session,
                    report=monthly_report,
                    value="123abc",
                    user_account=user,
                    metric_definition_key=law_enforcement.annual_budget.key,
                    current_time=current_time,
                )

    def test_get_datapoints(self) -> None:
        with SessionFactory.using_database(self.database_key) as session:
            monthly_report = self.test_schema_objects.test_report_monthly
            user = self.test_schema_objects.test_user_A
            session.add_all([monthly_report, user])
            session.flush()
            session.refresh(monthly_report)
            current_time = datetime.datetime(2022, 6, 1)

            DatapointInterface.add_datapoint(
                session=session,
                report=monthly_report,
                value="123",
                user_account=user,
                metric_definition_key=law_enforcement.calls_for_service.key,
                current_time=current_time,
            )

            report_ids = [
                monthly_report.id,
            ]

            datapoints = DatapointInterface.get_datapoints_with_report_ids(
                session=session,
                report_ids=report_ids,
                include_contexts=False,
            )

            assert len(datapoints) == 1
            assert datapoints[0].value == "123"

            datapoint_json = DatapointInterface.to_json_response(
                datapoint=datapoints[0],
                is_published=False,
                frequency=ReportingFrequency.MONTHLY,
            )

            self.assertDictEqual(
                datapoint_json,
                {
                    "id": monthly_report.id,
                    "report_id": 1,
                    "frequency": "MONTHLY",
                    "start_date": datetime.date(2022, 6, 1),
                    "end_date": datetime.date(2022, 7, 1),
                    "metric_definition_key": "LAW_ENFORCEMENT_CALLS_FOR_SERVICE_metric/law_enforcement/calls_for_service/type",
                    "metric_display_name": "Calls for Service",
                    "disaggregation_display_name": None,
                    "dimension_display_name": None,
                    "value": "123",
                    "is_published": False,
                },
            )
