# Recidiviz - a data platform for criminal justice reform
# Copyright (C) 2021 Recidiviz, Inc.
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
"""Tests for incarceration/identifier.py."""
import unittest
from datetime import date
from typing import Any, Dict, List, Optional
from unittest import mock

import attr
from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from recidiviz.calculator.pipeline.metrics.incarceration import identifier
from recidiviz.calculator.pipeline.metrics.incarceration.events import (
    IncarcerationAdmissionEvent,
    IncarcerationCommitmentFromSupervisionAdmissionEvent,
    IncarcerationEvent,
    IncarcerationReleaseEvent,
    IncarcerationStandardAdmissionEvent,
    IncarcerationStayEvent,
)
from recidiviz.calculator.pipeline.utils.assessment_utils import (
    DEFAULT_ASSESSMENT_SCORE_BUCKET,
)
from recidiviz.calculator.pipeline.utils.entity_normalization.normalized_incarceration_period_index import (
    NormalizedIncarcerationPeriodIndex,
)
from recidiviz.calculator.pipeline.utils.state_utils.state_calculation_config_manager import (
    get_all_state_specific_delegates,
    get_required_state_specific_delegates,
)
from recidiviz.calculator.pipeline.utils.state_utils.state_specific_commitment_from_supervision_delegate import (
    StateSpecificCommitmentFromSupervisionDelegate,
)
from recidiviz.calculator.pipeline.utils.state_utils.state_specific_incarceration_delegate import (
    StateSpecificIncarcerationDelegate,
)
from recidiviz.calculator.pipeline.utils.state_utils.state_specific_supervision_delegate import (
    StateSpecificSupervisionDelegate,
)
from recidiviz.calculator.pipeline.utils.state_utils.state_specific_violations_delegate import (
    StateSpecificViolationDelegate,
)
from recidiviz.calculator.pipeline.utils.state_utils.templates.us_xx.us_xx_commitment_from_supervision_utils import (
    UsXxCommitmentFromSupervisionDelegate,
)
from recidiviz.calculator.pipeline.utils.state_utils.templates.us_xx.us_xx_incarceration_delegate import (
    UsXxIncarcerationDelegate,
)
from recidiviz.calculator.pipeline.utils.state_utils.templates.us_xx.us_xx_supervision_delegate import (
    UsXxSupervisionDelegate,
)
from recidiviz.calculator.pipeline.utils.state_utils.templates.us_xx.us_xx_violations_delegate import (
    UsXxViolationDelegate,
)
from recidiviz.calculator.pipeline.utils.state_utils.us_id.us_id_incarceration_delegate import (
    UsIdIncarcerationDelegate,
)
from recidiviz.calculator.pipeline.utils.state_utils.us_id.us_id_supervision_delegate import (
    UsIdSupervisionDelegate,
)
from recidiviz.calculator.pipeline.utils.state_utils.us_mo.us_mo_incarceration_delegate import (
    UsMoIncarcerationDelegate,
)
from recidiviz.calculator.pipeline.utils.state_utils.us_mo.us_mo_sentence_classification import (
    SupervisionTypeSpan,
    UsMoSentenceStatus,
)
from recidiviz.calculator.pipeline.utils.state_utils.us_mo.us_mo_supervision_delegate import (
    UsMoSupervisionDelegate,
)
from recidiviz.calculator.pipeline.utils.state_utils.us_mo.us_mo_violations_delegate import (
    UsMoViolationDelegate,
)
from recidiviz.calculator.pipeline.utils.state_utils.us_nd.us_nd_commitment_from_supervision_delegate import (
    UsNdCommitmentFromSupervisionDelegate,
)
from recidiviz.calculator.pipeline.utils.state_utils.us_nd.us_nd_incarceration_delegate import (
    UsNdIncarcerationDelegate,
)
from recidiviz.calculator.pipeline.utils.state_utils.us_nd.us_nd_supervision_delegate import (
    UsNdSupervisionDelegate,
)
from recidiviz.calculator.pipeline.utils.state_utils.us_nd.us_nd_violations_delegate import (
    UsNdViolationDelegate,
)
from recidiviz.calculator.pipeline.utils.state_utils.us_pa.us_pa_incarceration_period_normalization_delegate import (
    SHOCK_INCARCERATION_9_MONTHS,
)
from recidiviz.common.constants.state.shared_enums import StateCustodialAuthority
from recidiviz.common.constants.state.state_assessment import (
    StateAssessmentLevel,
    StateAssessmentType,
)
from recidiviz.common.constants.state.state_case_type import StateSupervisionCaseType
from recidiviz.common.constants.state.state_incarceration import StateIncarcerationType
from recidiviz.common.constants.state.state_incarceration_period import (
    StateIncarcerationPeriodAdmissionReason,
    StateIncarcerationPeriodReleaseReason,
    StateSpecializedPurposeForIncarceration,
)
from recidiviz.common.constants.state.state_sentence import StateSentenceStatus
from recidiviz.common.constants.state.state_supervision_period import (
    StateSupervisionLevel,
    StateSupervisionPeriodSupervisionType,
    StateSupervisionPeriodTerminationReason,
)
from recidiviz.common.constants.state.state_supervision_sentence import (
    StateSupervisionSentenceSupervisionType,
)
from recidiviz.common.constants.state.state_supervision_violation import (
    StateSupervisionViolationType,
)
from recidiviz.common.constants.state.state_supervision_violation_response import (
    StateSupervisionViolationResponseDecidingBodyType,
    StateSupervisionViolationResponseDecision,
    StateSupervisionViolationResponseType,
)
from recidiviz.persistence.entity.state.entities import (
    StateAssessment,
    StateIncarcerationPeriod,
    StateIncarcerationSentence,
    StatePerson,
    StateSupervisionCaseTypeEntry,
    StateSupervisionPeriod,
    StateSupervisionSentence,
    StateSupervisionViolation,
    StateSupervisionViolationResponse,
    StateSupervisionViolationResponseDecisionEntry,
    StateSupervisionViolationTypeEntry,
)
from recidiviz.tests.calculator.pipeline.utils.entity_normalization.normalization_testing_utils import (
    default_normalized_ip_index_for_tests,
    default_normalized_sp_index_for_tests,
)
from recidiviz.tests.calculator.pipeline.utils.state_utils.state_calculation_config_manager_test import (
    STATE_DELEGATES_FOR_TESTS,
)
from recidiviz.tests.calculator.pipeline.utils.us_mo_fakes import (
    FakeUsMoIncarcerationSentence,
    FakeUsMoSupervisionSentence,
)

_STATE_CODE = "US_XX"
_COUNTY_OF_RESIDENCE = "county"
_COUNTY_OF_RESIDENCE_ROWS = [
    {
        "state_code": "US_XX",
        "person_id": 123,
        "county_of_residence": _COUNTY_OF_RESIDENCE,
    }
]

_DEFAULT_IP_ID = 123
_DEFAULT_SP_ID = 999
_DEFAULT_SSVR_ID = 789

_DEFAULT_INCARCERATION_PERIOD_JUDICIAL_DISTRICT_ASSOCIATION = [
    {"incarceration_period_id": _DEFAULT_IP_ID, "judicial_district_code": "NW"}
]

_DEFAULT_SUPERVISION_PERIOD_AGENT_ASSOCIATIONS = {
    _DEFAULT_SP_ID: {
        "agent_id": 000,
        "agent_external_id": "XXX",
        "supervision_period_id": _DEFAULT_SP_ID,
    }
}

_DEFAULT_SUPERVISION_PERIOD_AGENT_ASSOCIATION_LIST = list(
    _DEFAULT_SUPERVISION_PERIOD_AGENT_ASSOCIATIONS.values()
)


class TestFindIncarcerationEvents(unittest.TestCase):
    """Tests the find_incarceration_events function."""

    def setUp(self) -> None:
        self.identifier = identifier.IncarcerationIdentifier()
        self.person = StatePerson.new_with_defaults(state_code="US_XX")

    def _run_find_incarceration_events(
        self,
        incarceration_periods: Optional[List[StateIncarcerationPeriod]] = None,
        incarceration_sentences: Optional[List[StateIncarcerationSentence]] = None,
        supervision_sentences: Optional[List[StateSupervisionSentence]] = None,
        supervision_periods: Optional[List[StateSupervisionPeriod]] = None,
        assessments: Optional[List[StateAssessment]] = None,
        violation_responses: Optional[List[StateSupervisionViolationResponse]] = None,
        supervision_period_to_agent_association: Optional[List[Dict[str, Any]]] = None,
        state_code_override: Optional[str] = None,
    ) -> List[IncarcerationEvent]:
        """Helper for testing the find_events function on the identifier."""

        state_specific_delegate_patcher = mock.patch(
            "recidiviz.calculator.pipeline.utils.state_utils"
            ".state_calculation_config_manager.get_all_state_specific_delegates",
            return_value=STATE_DELEGATES_FOR_TESTS,
        )
        if not state_code_override:
            state_specific_delegate_patcher.start()

        required_delegates = get_required_state_specific_delegates(
            state_code=(state_code_override or _STATE_CODE),
            required_delegates=self.identifier.required_state_specific_delegates(),
        )

        if not state_code_override:
            state_specific_delegate_patcher.stop()

        all_kwargs = {
            **required_delegates,
            StateIncarcerationPeriod.__name__: incarceration_periods or [],
            StateIncarcerationSentence.__name__: incarceration_sentences or [],
            StateSupervisionSentence.__name__: supervision_sentences or [],
            StateSupervisionPeriod.__name__: supervision_periods or [],
            StateAssessment.__name__: assessments or [],
            StateSupervisionViolationResponse.__name__: violation_responses or [],
            "supervision_period_to_agent_association": (
                supervision_period_to_agent_association
                or _DEFAULT_SUPERVISION_PERIOD_AGENT_ASSOCIATION_LIST
            ),
            "incarceration_period_judicial_district_association": _DEFAULT_INCARCERATION_PERIOD_JUDICIAL_DISTRICT_ASSOCIATION,
            "persons_to_recent_county_of_residence": _COUNTY_OF_RESIDENCE_ROWS,
        }
        return self.identifier.find_events(self.person, all_kwargs)

    def test_find_incarceration_events(self) -> None:
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=_DEFAULT_IP_ID,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            facility="PRISON3",
            admission_date=date(2008, 11, 20),
            admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            admission_reason_raw_text="INCARCERATION_ADMISSION",
            release_date=date(2009, 1, 4),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )

        incarceration_sentence = StateIncarcerationSentence.new_with_defaults(
            state_code="US_XX",
            start_date=date(2008, 10, 11),
            status=StateSentenceStatus.PRESENT_WITHOUT_INFO,
        )

        incarceration_events = self._run_find_incarceration_events(
            incarceration_periods=[incarceration_period],
            incarceration_sentences=[incarceration_sentence],
        )

        assert incarceration_period.admission_date is not None
        assert incarceration_period.release_date is not None
        expected_events = [
            *expected_incarceration_stay_events(
                incarceration_period,
                judicial_district_code="NW",
            ),
            IncarcerationStandardAdmissionEvent(
                state_code=incarceration_period.state_code,
                event_date=incarceration_period.admission_date,
                facility=incarceration_period.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
                admission_reason_raw_text="INCARCERATION_ADMISSION",
                specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            ),
            IncarcerationReleaseEvent(
                state_code=incarceration_period.state_code,
                event_date=incarceration_period.release_date,
                facility=incarceration_period.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
                admission_reason=incarceration_period.admission_reason,
                total_days_incarcerated=(
                    incarceration_period.release_date
                    - incarceration_period.admission_date
                ).days,
                purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            ),
        ]

        self.assertCountEqual(expected_events, incarceration_events)

    def test_find_incarceration_events_transfer(self) -> None:
        incarceration_period_1 = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=_DEFAULT_IP_ID,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            facility="PRISON3",
            admission_date=date(2009, 11, 20),
            admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            admission_reason_raw_text="NA",
            release_date=date(2009, 12, 1),
            release_reason=StateIncarcerationPeriodReleaseReason.TRANSFER,
        )

        incarceration_period_2 = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=2222,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            facility="PRISON 10",
            admission_date=date(2009, 12, 1),
            admission_reason=StateIncarcerationPeriodAdmissionReason.TRANSFER,
            release_date=date(2010, 2, 4),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
        )

        incarceration_sentence = StateIncarcerationSentence.new_with_defaults(
            state_code="US_XX",
            start_date=date(2008, 1, 11),
            status=StateSentenceStatus.PRESENT_WITHOUT_INFO,
        )

        incarceration_events = self._run_find_incarceration_events(
            incarceration_periods=[incarceration_period_1, incarceration_period_2],
            incarceration_sentences=[incarceration_sentence],
        )

        assert incarceration_period_1.admission_date is not None
        assert incarceration_period_2.release_date is not None
        expected_events = [
            *expected_incarceration_stay_events(
                incarceration_period_1,
                judicial_district_code="NW",
            ),
            *expected_incarceration_stay_events(
                incarceration_period_2,
                original_admission_reason=incarceration_period_1.admission_reason,
                original_admission_reason_raw_text=incarceration_period_1.admission_reason_raw_text,
            ),
            IncarcerationStandardAdmissionEvent(
                state_code=incarceration_period_1.state_code,
                event_date=incarceration_period_1.admission_date,
                facility=incarceration_period_1.facility,
                admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
                admission_reason_raw_text="NA",
                county_of_residence=_COUNTY_OF_RESIDENCE,
                specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            ),
            IncarcerationReleaseEvent(
                state_code=incarceration_period_2.state_code,
                event_date=incarceration_period_2.release_date,
                facility=incarceration_period_2.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
                admission_reason=incarceration_period_1.admission_reason,
                total_days_incarcerated=(
                    incarceration_period_2.release_date
                    - incarceration_period_1.admission_date
                ).days,
                purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            ),
        ]

        self.assertCountEqual(expected_events, incarceration_events)

    def test_find_incarceration_events_revocation_then_escape(self) -> None:
        supervision_period = StateSupervisionPeriod.new_with_defaults(
            supervision_period_id=_DEFAULT_SP_ID,
            external_id="XY2",
            state_code="US_XX",
            start_date=date(2001, 3, 13),
            termination_date=date(2008, 12, 20),
            supervision_site="X",
            supervision_type=StateSupervisionPeriodSupervisionType.PROBATION,
        )

        incarceration_period_1 = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=_DEFAULT_IP_ID,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            facility="PRISON3",
            admission_date=date(2009, 1, 20),
            admission_reason=StateIncarcerationPeriodAdmissionReason.REVOCATION,
            release_date=date(2009, 12, 1),
            release_reason=StateIncarcerationPeriodReleaseReason.ESCAPE,
        )

        incarceration_period_2 = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=2222,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            facility="PRISON 10",
            admission_date=date(2009, 12, 20),
            admission_reason=StateIncarcerationPeriodAdmissionReason.RETURN_FROM_ESCAPE,
            release_date=date(2010, 2, 4),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
        )

        incarceration_events = self._run_find_incarceration_events(
            incarceration_periods=[incarceration_period_1, incarceration_period_2],
            supervision_periods=[supervision_period],
        )

        assert incarceration_period_1.admission_date is not None
        assert incarceration_period_1.release_date is not None
        assert incarceration_period_2.admission_date is not None
        assert incarceration_period_2.release_date is not None
        expected_events = [
            *expected_incarceration_stay_events(
                incarceration_period_1,
                judicial_district_code="NW",
                commitment_from_supervision_supervision_type=StateSupervisionPeriodSupervisionType.PROBATION,
            ),
            *expected_incarceration_stay_events(
                incarceration_period_2,
                original_admission_reason=incarceration_period_1.admission_reason,
                original_admission_reason_raw_text=incarceration_period_1.admission_reason_raw_text,
                commitment_from_supervision_supervision_type=StateSupervisionPeriodSupervisionType.PROBATION,
            ),
            IncarcerationCommitmentFromSupervisionAdmissionEvent(
                state_code=incarceration_period_1.state_code,
                event_date=incarceration_period_1.admission_date,
                facility=incarceration_period_1.facility,
                admission_reason=StateIncarcerationPeriodAdmissionReason.REVOCATION,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
                supervision_type=StateSupervisionPeriodSupervisionType.PROBATION,
                supervising_district_external_id="X",
                level_1_supervision_location_external_id="X",
                supervising_officer_external_id="XXX",
                case_type=StateSupervisionCaseType.GENERAL,
                assessment_score_bucket=DEFAULT_ASSESSMENT_SCORE_BUCKET,
            ),
            IncarcerationStandardAdmissionEvent(
                state_code=incarceration_period_2.state_code,
                event_date=incarceration_period_2.admission_date,
                facility=incarceration_period_2.facility,
                admission_reason=StateIncarcerationPeriodAdmissionReason.RETURN_FROM_ESCAPE,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            ),
            IncarcerationReleaseEvent(
                state_code=incarceration_period_1.state_code,
                event_date=incarceration_period_1.release_date,
                facility=incarceration_period_1.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                release_reason=StateIncarcerationPeriodReleaseReason.ESCAPE,
                admission_reason=incarceration_period_1.admission_reason,
                total_days_incarcerated=(
                    incarceration_period_1.release_date
                    - incarceration_period_1.admission_date
                ).days,
                purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
                commitment_from_supervision_supervision_type=StateSupervisionPeriodSupervisionType.PROBATION,
            ),
            IncarcerationReleaseEvent(
                state_code=incarceration_period_2.state_code,
                event_date=incarceration_period_2.release_date,
                facility=incarceration_period_2.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
                admission_reason=incarceration_period_1.admission_reason,
                total_days_incarcerated=(
                    incarceration_period_2.release_date
                    - incarceration_period_2.admission_date
                ).days,
                purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
                commitment_from_supervision_supervision_type=StateSupervisionPeriodSupervisionType.PROBATION,
            ),
        ]

        self.assertCountEqual(expected_events, incarceration_events)

    def test_find_incarceration_events_transfer_status_change(self) -> None:
        """Tests that adjacent IPs with TRANSFER edges are updated to have STATUS_CHANGE
        release and admission reasons when the IPs have different
        specialized_purpose_for_incarceration values.
        """
        state_code = "US_XX"
        incarceration_period_1 = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code=state_code,
            facility="PRISON3",
            admission_date=date(2013, 11, 20),
            admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.SHOCK_INCARCERATION,
            release_date=date(2019, 12, 4),
            release_reason=StateIncarcerationPeriodReleaseReason.TRANSFER,
        )

        incarceration_period_2 = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=2222,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code=state_code,
            facility="PRISON3",
            admission_date=date(2019, 12, 4),
            admission_reason=StateIncarcerationPeriodAdmissionReason.TRANSFER,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            release_date=date(2019, 12, 8),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
        )

        incarceration_sentence = StateIncarcerationSentence.new_with_defaults(
            state_code=state_code,
            incarceration_sentence_id=111,
            start_date=date(2017, 1, 1),
            status=StateSentenceStatus.COMPLETED,
        )

        incarceration_events = self._run_find_incarceration_events(
            incarceration_periods=[incarceration_period_1, incarceration_period_2],
            incarceration_sentences=[incarceration_sentence],
        )

        assert incarceration_period_1.admission_date is not None
        assert incarceration_period_1.release_date is not None
        assert incarceration_period_2.admission_date is not None
        assert incarceration_period_2.release_date is not None
        assert incarceration_period_2.release_reason is not None
        expected_events = [
            *expected_incarceration_stay_events(incarceration_period_1),
            *expected_incarceration_stay_events(
                incarceration_period_2,
                original_admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            ),
            IncarcerationStandardAdmissionEvent(
                state_code=incarceration_period_1.state_code,
                event_date=incarceration_period_1.admission_date,
                facility=incarceration_period_1.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
                specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.SHOCK_INCARCERATION,
            ),
            IncarcerationReleaseEvent(
                state_code=incarceration_period_1.state_code,
                event_date=incarceration_period_1.release_date,
                facility=incarceration_period_1.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                release_reason=StateIncarcerationPeriodReleaseReason.STATUS_CHANGE,
                release_reason_raw_text=incarceration_period_1.release_reason_raw_text,
                admission_reason=incarceration_period_1.admission_reason,
                total_days_incarcerated=(
                    incarceration_period_1.release_date
                    - incarceration_period_1.admission_date
                ).days,
                purpose_for_incarceration=StateSpecializedPurposeForIncarceration.SHOCK_INCARCERATION,
            ),
            IncarcerationStandardAdmissionEvent(
                state_code=incarceration_period_2.state_code,
                event_date=incarceration_period_2.admission_date,
                facility=incarceration_period_2.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                admission_reason=StateIncarcerationPeriodAdmissionReason.STATUS_CHANGE,
                specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            ),
            IncarcerationReleaseEvent(
                state_code=incarceration_period_2.state_code,
                event_date=incarceration_period_2.release_date,
                facility=incarceration_period_2.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                release_reason=incarceration_period_2.release_reason,
                release_reason_raw_text=incarceration_period_2.release_reason_raw_text,
                admission_reason=incarceration_period_1.admission_reason,
                total_days_incarcerated=(
                    incarceration_period_2.release_date
                    - incarceration_period_2.admission_date
                ).days,
                purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            ),
        ]

        self.assertCountEqual(expected_events, incarceration_events)

    def test_find_incarceration_events_multiple_sentences(self) -> None:
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=_DEFAULT_IP_ID,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            facility="PRISON3",
            admission_date=date(2008, 11, 20),
            admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            release_date=date(2009, 1, 4),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
        )

        incarceration_sentence = StateIncarcerationSentence.new_with_defaults(
            state_code="US_XX",
            start_date=date(2008, 10, 11),
            status=StateSentenceStatus.PRESENT_WITHOUT_INFO,
        )

        supervision_sentence = StateSupervisionSentence.new_with_defaults(
            state_code="US_XX",
            start_date=date(2008, 10, 11),
            status=StateSentenceStatus.PRESENT_WITHOUT_INFO,
        )

        incarceration_events = self._run_find_incarceration_events(
            incarceration_periods=[incarceration_period],
            incarceration_sentences=[incarceration_sentence],
            supervision_sentences=[supervision_sentence],
        )

        assert incarceration_period.admission_date is not None
        assert incarceration_period.release_date is not None
        expected_events: List[IncarcerationEvent] = [
            *expected_incarceration_stay_events(
                incarceration_period, judicial_district_code="NW"
            ),
            IncarcerationStandardAdmissionEvent(
                state_code=incarceration_period.state_code,
                event_date=incarceration_period.admission_date,
                facility=incarceration_period.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
                specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            ),
            IncarcerationReleaseEvent(
                state_code=incarceration_period.state_code,
                event_date=incarceration_period.release_date,
                facility=incarceration_period.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
                admission_reason=incarceration_period.admission_reason,
                total_days_incarcerated=(
                    incarceration_period.release_date
                    - incarceration_period.admission_date
                ).days,
                purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            ),
        ]

        self.assertCountEqual(expected_events, incarceration_events)

    def test_find_incarceration_events_multiple_sentences_with_investigative_supervision_period_us_id(
        self,
    ) -> None:

        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=_DEFAULT_IP_ID,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_ID",
            facility="PRISON3",
            admission_date=date(2018, 11, 20),
            admission_reason=StateIncarcerationPeriodAdmissionReason.ADMITTED_FROM_SUPERVISION,
            release_date=date(2018, 11, 21),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
        )

        incarceration_sentence = StateIncarcerationSentence.new_with_defaults(
            state_code="US_ID",
            start_date=date(2018, 11, 20),
            status=StateSentenceStatus.PRESENT_WITHOUT_INFO,
        )

        supervision_period = StateSupervisionPeriod.new_with_defaults(
            supervision_period_id=1111,
            state_code="US_ID",
            start_date=date(2018, 11, 1),
            termination_date=date(2018, 11, 19),
            supervision_type=StateSupervisionPeriodSupervisionType.INVESTIGATION,
        )

        supervision_sentence = StateSupervisionSentence.new_with_defaults(
            state_code="US_ID",
            start_date=date(2018, 11, 1),
            status=StateSentenceStatus.PRESENT_WITHOUT_INFO,
        )

        incarceration_events = self._run_find_incarceration_events(
            state_code_override="US_ID",
            incarceration_periods=[incarceration_period],
            incarceration_sentences=[incarceration_sentence],
            supervision_sentences=[supervision_sentence],
            supervision_periods=[supervision_period],
        )

        assert incarceration_period.admission_date is not None
        assert incarceration_period.release_date is not None
        expected_events = [
            *expected_incarceration_stay_events(
                incarceration_period,
                judicial_district_code="NW",
                original_admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            ),
            IncarcerationStandardAdmissionEvent(
                state_code=incarceration_period.state_code,
                event_date=incarceration_period.admission_date,
                facility=incarceration_period.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
                specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            ),
            IncarcerationReleaseEvent(
                state_code=incarceration_period.state_code,
                event_date=incarceration_period.release_date,
                facility=incarceration_period.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
                admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
                total_days_incarcerated=(
                    incarceration_period.release_date
                    - incarceration_period.admission_date
                ).days,
                purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            ),
        ]

        self.assertCountEqual(expected_events, incarceration_events)

    def test_find_incarceration_events_purpose_for_incarceration_change_us_id(
        self,
    ) -> None:
        """Tests that with state code US_ID, treatment in prison periods that are followed by a transfer to general
        result in the correct IncarcerationStayEvents, IncarcerationAdmissionEvents, and
        IncarcerationReleaseEvents with updated STATUS_CHANGE reasons"""

        treatment_incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=_DEFAULT_IP_ID,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_ID",
            facility="PRISON3",
            admission_date=date(2009, 11, 29),
            admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            admission_reason_raw_text="NA",
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.TREATMENT_IN_PRISON,
            release_date=date(2009, 12, 1),
            release_reason=StateIncarcerationPeriodReleaseReason.TRANSFER,
        )

        general_incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=2222,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_ID",
            facility="PRISON 10",
            admission_date=date(2009, 12, 1),
            admission_reason=StateIncarcerationPeriodAdmissionReason.TRANSFER,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            release_date=date(2009, 12, 3),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
        )

        incarceration_sentence = StateIncarcerationSentence.new_with_defaults(
            state_code="US_ID",
            start_date=date(2008, 1, 11),
            status=StateSentenceStatus.PRESENT_WITHOUT_INFO,
        )

        incarceration_events = self._run_find_incarceration_events(
            state_code_override="US_ID",
            incarceration_periods=[
                treatment_incarceration_period,
                general_incarceration_period,
            ],
            incarceration_sentences=[incarceration_sentence],
        )

        assert general_incarceration_period.admission_date is not None
        assert treatment_incarceration_period.release_date is not None
        assert treatment_incarceration_period.admission_date is not None
        assert general_incarceration_period.release_date is not None
        assert general_incarceration_period.admission_date is not None
        expected_events: List[IncarcerationEvent] = [
            *expected_incarceration_stay_events(
                treatment_incarceration_period,
                judicial_district_code="NW",
            ),
            *expected_incarceration_stay_events(
                general_incarceration_period,
                original_admission_reason=treatment_incarceration_period.admission_reason,
                original_admission_reason_raw_text=treatment_incarceration_period.admission_reason_raw_text,
            ),
            IncarcerationStandardAdmissionEvent(
                state_code=treatment_incarceration_period.state_code,
                event_date=treatment_incarceration_period.admission_date,
                facility=treatment_incarceration_period.facility,
                admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
                admission_reason_raw_text="NA",
                county_of_residence=_COUNTY_OF_RESIDENCE,
                specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.TREATMENT_IN_PRISON,
            ),
            IncarcerationStandardAdmissionEvent(
                state_code=general_incarceration_period.state_code,
                event_date=general_incarceration_period.admission_date,
                facility=general_incarceration_period.facility,
                admission_reason=StateIncarcerationPeriodAdmissionReason.STATUS_CHANGE,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            ),
            IncarcerationReleaseEvent(
                state_code=treatment_incarceration_period.state_code,
                event_date=treatment_incarceration_period.release_date,
                facility=treatment_incarceration_period.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                release_reason=StateIncarcerationPeriodReleaseReason.STATUS_CHANGE,
                purpose_for_incarceration=treatment_incarceration_period.specialized_purpose_for_incarceration,
                admission_reason=treatment_incarceration_period.admission_reason,
                total_days_incarcerated=(
                    treatment_incarceration_period.release_date
                    - treatment_incarceration_period.admission_date
                ).days,
            ),
            IncarcerationReleaseEvent(
                state_code=general_incarceration_period.state_code,
                event_date=general_incarceration_period.release_date,
                facility=general_incarceration_period.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
                admission_reason=treatment_incarceration_period.admission_reason,
                purpose_for_incarceration=general_incarceration_period.specialized_purpose_for_incarceration,
                total_days_incarcerated=(
                    general_incarceration_period.release_date
                    - general_incarceration_period.admission_date
                ).days,
            ),
        ]

        self.assertCountEqual(expected_events, incarceration_events)

    @freeze_time("2000-01-01")
    def test_find_incarceration_events_dates_in_future(self) -> None:
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=_DEFAULT_IP_ID,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            facility="PRISON3",
            admission_date=date(1990, 1, 1),
            admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            admission_reason_raw_text="INCARCERATION_ADMISSION",
            # Erroneous release_date in the future
            release_date=date(2009, 1, 4),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )

        incarceration_period_in_future = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=_DEFAULT_IP_ID,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            facility="PRISON3",
            # Erroneous admission_date in the future, period should be dropped entirely
            admission_date=date(2010, 1, 1),
            admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            admission_reason_raw_text="INCARCERATION_ADMISSION",
            release_date=date(2010, 1, 4),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )

        incarceration_sentence = StateIncarcerationSentence.new_with_defaults(
            state_code="US_XX",
            status=StateSentenceStatus.PRESENT_WITHOUT_INFO,
            start_date=date(1989, 11, 1),
        )

        incarceration_events = self._run_find_incarceration_events(
            incarceration_periods=[
                incarceration_period,
                incarceration_period_in_future,
            ],
            incarceration_sentences=[incarceration_sentence],
        )
        assert incarceration_period.admission_date is not None
        expected_events = [
            *expected_incarceration_stay_events(
                incarceration_period,
                judicial_district_code="NW",
            ),
            IncarcerationStandardAdmissionEvent(
                state_code=incarceration_period.state_code,
                event_date=incarceration_period.admission_date,
                facility=incarceration_period.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
                admission_reason_raw_text="INCARCERATION_ADMISSION",
                specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            ),
        ]

        self.assertCountEqual(expected_events, incarceration_events)

    def testFindIncarcerationEvents_only_placeholder_ips_and_sps(self) -> None:
        supervision_period = StateSupervisionPeriod.new_with_defaults(
            supervision_period_id=_DEFAULT_SP_ID,
            state_code="US_XX",
        )
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=_DEFAULT_IP_ID,
            state_code="US_XX",
        )

        incarceration_sentence = StateIncarcerationSentence.new_with_defaults(
            state_code="US_XX",
            start_date=date(2008, 10, 11),
            status=StateSentenceStatus.PRESENT_WITHOUT_INFO,
        )

        supervision_sentence = StateSupervisionSentence.new_with_defaults(
            state_code="US_XX",
            start_date=date(2008, 10, 11),
            status=StateSentenceStatus.PRESENT_WITHOUT_INFO,
        )

        incarceration_events = self._run_find_incarceration_events(
            incarceration_periods=[incarceration_period],
            incarceration_sentences=[incarceration_sentence],
            supervision_sentences=[supervision_sentence],
            supervision_periods=[supervision_period],
        )

        self.assertCountEqual([], incarceration_events)

    def testFindIncarcerationEvents_usNd_tempCustodyFollowedByRevocation(self) -> None:
        """Tests that with state code US_ND, only periods with a custodial_authority of
        STATE_PRISON are included in the population.
        """

        temp_custody_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            external_id="1",
            incarceration_type=StateIncarcerationType.EXTERNAL_UNKNOWN,
            state_code="US_ND",
            facility="NTAD",
            custodial_authority=StateCustodialAuthority.EXTERNAL_UNKNOWN,
            admission_date=date(2018, 11, 20),
            admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            admission_reason_raw_text="ADMN",
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.TEMPORARY_CUSTODY,
            release_date=date(2018, 12, 20),
            release_reason=StateIncarcerationPeriodReleaseReason.CONDITIONAL_RELEASE,
            release_reason_raw_text="RPAR",
        )

        supervision_violation = StateSupervisionViolation.new_with_defaults(
            supervision_violation_id=123455,
            state_code="US_ND",
            violation_date=date(2018, 4, 20),
            supervision_violation_types=[
                StateSupervisionViolationTypeEntry.new_with_defaults(
                    state_code="US_ND",
                    violation_type=StateSupervisionViolationType.FELONY,
                ),
            ],
        )

        ssvr = StateSupervisionViolationResponse.new_with_defaults(
            state_code="US_ND",
            supervision_violation_response_id=_DEFAULT_SSVR_ID,
            supervision_violation=supervision_violation,
            response_date=date(2008, 12, 25),
            response_type=StateSupervisionViolationResponseType.PERMANENT_DECISION,
        )

        duplicate_supervision_violation = StateSupervisionViolation.new_with_defaults(
            supervision_violation_id=123455,
            state_code="US_ND",
            supervision_violation_types=[
                StateSupervisionViolationTypeEntry.new_with_defaults(
                    state_code="US_ND",
                    violation_type=StateSupervisionViolationType.FELONY,
                ),
            ],
        )

        duplicate_ssvr = StateSupervisionViolationResponse.new_with_defaults(
            state_code="US_ND",
            supervision_violation_response_id=_DEFAULT_SSVR_ID,
            supervision_violation=duplicate_supervision_violation,
            response_date=date(2008, 12, 25),
            response_type=StateSupervisionViolationResponseType.PERMANENT_DECISION,
        )

        revocation_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=_DEFAULT_IP_ID,
            external_id="2",
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_ND",
            facility="PRISON",
            admission_date=date(2008, 12, 20),
            admission_reason=StateIncarcerationPeriodAdmissionReason.REVOCATION,
            admission_reason_raw_text="NPRB",
            release_date=date(2008, 12, 21),
            release_reason=StateIncarcerationPeriodReleaseReason.CONDITIONAL_RELEASE,
            release_reason_raw_text="PV",
            custodial_authority=StateCustodialAuthority.STATE_PRISON,
        )

        revoked_supervision_period = StateSupervisionPeriod.new_with_defaults(
            supervision_period_id=_DEFAULT_SP_ID,
            external_id="XY2",
            state_code="US_ND",
            start_date=date(2001, 3, 13),
            termination_date=date(2008, 12, 20),
            supervision_site="X",
            supervision_type=StateSupervisionPeriodSupervisionType.PROBATION,
        )

        post_revocation_supervision_period = StateSupervisionPeriod.new_with_defaults(
            supervision_period_id=_DEFAULT_SP_ID + 1,
            external_id="XY3",
            state_code="US_ND",
            start_date=date(2008, 12, 21),
            termination_date=None,
            supervision_site="X",
            supervision_type=StateSupervisionPeriodSupervisionType.PROBATION,
        )

        incarceration_sentence = StateIncarcerationSentence.new_with_defaults(
            state_code="US_ND",
            start_date=date(2008, 12, 11),
            status=StateSentenceStatus.PRESENT_WITHOUT_INFO,
        )

        incarceration_events = self._run_find_incarceration_events(
            state_code_override="US_ND",
            incarceration_periods=[temp_custody_period, revocation_period],
            incarceration_sentences=[incarceration_sentence],
            supervision_periods=[
                revoked_supervision_period,
                post_revocation_supervision_period,
            ],
            violation_responses=[ssvr, duplicate_ssvr],
        )

        assert temp_custody_period.admission_date is not None
        assert temp_custody_period.admission_reason is not None
        assert temp_custody_period.release_reason is not None
        assert temp_custody_period.release_date is not None
        assert revocation_period.release_date is not None
        assert revocation_period.release_reason is not None
        assert revocation_period.admission_date is not None
        assert revocation_period.admission_reason is not None

        expected_events: List[IncarcerationEvent] = [
            *expected_incarceration_stay_events(
                temp_custody_period,
                original_admission_reason=StateIncarcerationPeriodAdmissionReason.TEMPORARY_CUSTODY,
                included_in_state_population=False,
            ),
            IncarcerationStandardAdmissionEvent(
                state_code=temp_custody_period.state_code,
                event_date=temp_custody_period.admission_date,
                facility=temp_custody_period.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                admission_reason=StateIncarcerationPeriodAdmissionReason.TEMPORARY_CUSTODY,
                admission_reason_raw_text=temp_custody_period.admission_reason_raw_text,
                specialized_purpose_for_incarceration=temp_custody_period.specialized_purpose_for_incarceration,
                included_in_state_population=False,
            ),
            IncarcerationReleaseEvent(
                state_code=temp_custody_period.state_code,
                event_date=temp_custody_period.release_date,
                facility=temp_custody_period.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                release_reason=StateIncarcerationPeriodReleaseReason.RELEASED_FROM_TEMPORARY_CUSTODY,
                release_reason_raw_text=temp_custody_period.release_reason_raw_text,
                admission_reason=StateIncarcerationPeriodAdmissionReason.TEMPORARY_CUSTODY,
                total_days_incarcerated=(
                    temp_custody_period.release_date
                    - temp_custody_period.admission_date
                ).days,
                purpose_for_incarceration=temp_custody_period.specialized_purpose_for_incarceration,
                included_in_state_population=False,
                supervision_type_at_release=StateSupervisionPeriodSupervisionType.PROBATION,
            ),
            IncarcerationStayEvent(
                admission_reason=revocation_period.admission_reason,
                admission_reason_raw_text=revocation_period.admission_reason_raw_text,
                state_code=revocation_period.state_code,
                event_date=revocation_period.admission_date,
                facility=revocation_period.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                judicial_district_code="NW",
                specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
                commitment_from_supervision_supervision_type=StateSupervisionPeriodSupervisionType.PROBATION,
            ),
            IncarcerationCommitmentFromSupervisionAdmissionEvent(
                state_code=revoked_supervision_period.state_code,
                event_date=revocation_period.admission_date,
                facility=revocation_period.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                admission_reason=revocation_period.admission_reason,
                admission_reason_raw_text=revocation_period.admission_reason_raw_text,
                supervision_type=StateSupervisionPeriodSupervisionType.PROBATION,
                case_type=StateSupervisionCaseType.GENERAL,
                specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
                most_severe_violation_type=StateSupervisionViolationType.FELONY,
                most_severe_violation_type_subtype=StateSupervisionViolationType.FELONY.value,
                # Duplicate responses were merged in pre-processing
                response_count=1,
                violation_history_description="1felony",
                violation_type_frequency_counter=[["FELONY"]],
                supervising_officer_external_id="XXX",
                supervising_district_external_id="X",
                level_1_supervision_location_external_id="X",
                assessment_score_bucket=DEFAULT_ASSESSMENT_SCORE_BUCKET,
            ),
            IncarcerationReleaseEvent(
                state_code=revocation_period.state_code,
                event_date=revocation_period.release_date,
                facility=revocation_period.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                release_reason=revocation_period.release_reason,
                release_reason_raw_text=revocation_period.release_reason_raw_text,
                supervision_type_at_release=StateSupervisionPeriodSupervisionType.PROBATION,
                commitment_from_supervision_supervision_type=StateSupervisionPeriodSupervisionType.PROBATION,
                admission_reason=revocation_period.admission_reason,
                total_days_incarcerated=(
                    revocation_period.release_date - revocation_period.admission_date
                ).days,
                purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            ),
        ]

        self.assertCountEqual(
            expected_events,
            incarceration_events,
        )

    def testFindIncarcerationEvents_usMo_tempCustodyFollowedByRevocation(self) -> None:
        """Tests that when a temporary custody period is followed by a revocation
        period.
        """

        temp_custody_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            external_id="1",
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_MO",
            facility="PRISON",
            admission_date=date(2008, 11, 20),
            admission_reason=StateIncarcerationPeriodAdmissionReason.TEMPORARY_CUSTODY,
            admission_reason_raw_text="40I0050",
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            specialized_purpose_for_incarceration_raw_text="S",
            release_date=date(2008, 11, 21),
            release_reason=StateIncarcerationPeriodReleaseReason.RELEASED_FROM_TEMPORARY_CUSTODY,
        )
        revocation_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1112,
            external_id="2",
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_MO",
            facility="PRISON",
            admission_date=date(2008, 11, 21),
            admission_reason=StateIncarcerationPeriodAdmissionReason.REVOCATION,
            admission_reason_raw_text="40I2000",
            release_date=date(2008, 11, 22),
            release_reason=StateIncarcerationPeriodReleaseReason.CONDITIONAL_RELEASE,
        )

        supervision_period = StateSupervisionPeriod.new_with_defaults(
            state_code="US_MO",
            supervision_period_id=1313,
            external_id="3",
            start_date=date(2008, 1, 1),
            supervision_level=StateSupervisionLevel.MEDIUM,
        )

        assert revocation_period.admission_date is not None
        assert supervision_period.start_date is not None
        assert temp_custody_period.admission_date is not None
        incarceration_sentence = (
            FakeUsMoIncarcerationSentence.fake_sentence_from_sentence(
                StateIncarcerationSentence.new_with_defaults(
                    state_code="US_MO",
                    incarceration_sentence_id=123,
                    status=StateSentenceStatus.PRESENT_WITHOUT_INFO,
                    start_date=date(2008, 1, 1),
                ),
                supervision_type_spans=[
                    SupervisionTypeSpan(
                        start_date=supervision_period.start_date,
                        end_date=temp_custody_period.admission_date,
                        supervision_type=StateSupervisionSentenceSupervisionType.PAROLE,
                        start_critical_statuses=[
                            UsMoSentenceStatus(
                                sentence_external_id="123",
                                sentence_status_external_id="test-status-1",
                                status_date=temp_custody_period.admission_date,
                                status_code="40O1010",
                                status_description="Parole Release",
                                person_external_id="1",
                                is_supervision_type_critical_status=False,
                                is_supervision_out_status=False,
                                is_supervision_in_status=False,
                                is_incarceration_in_status=True,
                                is_incarceration_out_status=False,
                                is_lifetime_supervision_start_status=False,
                                is_sentence_termination_status_candidate=False,
                                is_investigation_status=False,
                                is_sentence_termimination_status=False,
                            ),
                        ],
                        end_critical_statuses=[
                            UsMoSentenceStatus(
                                sentence_external_id="123",
                                sentence_status_external_id="test-status-1",
                                status_date=temp_custody_period.admission_date,
                                status_code="40O1020",
                                status_description="Parole To Custody/Detainer",
                                person_external_id="1",
                                is_supervision_type_critical_status=False,
                                is_supervision_out_status=False,
                                is_supervision_in_status=False,
                                is_incarceration_in_status=True,
                                is_incarceration_out_status=False,
                                is_lifetime_supervision_start_status=False,
                                is_sentence_termination_status_candidate=False,
                                is_investigation_status=False,
                                is_sentence_termimination_status=False,
                            ),
                        ],
                    ),
                    SupervisionTypeSpan(
                        start_date=temp_custody_period.admission_date,
                        end_date=revocation_period.admission_date,
                        supervision_type=None,
                        start_critical_statuses=[
                            UsMoSentenceStatus(
                                sentence_external_id="123",
                                sentence_status_external_id="test-status-1",
                                status_date=temp_custody_period.admission_date,
                                status_code="40I0050",
                                status_description="Board Holdover",
                                person_external_id="1",
                                is_supervision_type_critical_status=False,
                                is_supervision_out_status=False,
                                is_supervision_in_status=False,
                                is_incarceration_in_status=True,
                                is_incarceration_out_status=False,
                                is_lifetime_supervision_start_status=False,
                                is_sentence_termination_status_candidate=False,
                                is_investigation_status=False,
                                is_sentence_termimination_status=False,
                            ),
                        ],
                        end_critical_statuses=[
                            UsMoSentenceStatus(
                                sentence_external_id="123",
                                sentence_status_external_id="test-status-1",
                                status_date=revocation_period.admission_date,
                                status_code="50N1050",
                                status_description="Parole Viol Upd-Fel Law Viol",
                                person_external_id="1",
                                is_supervision_type_critical_status=False,
                                is_supervision_out_status=False,
                                is_supervision_in_status=False,
                                is_incarceration_in_status=True,
                                is_incarceration_out_status=False,
                                is_lifetime_supervision_start_status=False,
                                is_sentence_termination_status_candidate=False,
                                is_investigation_status=False,
                                is_sentence_termimination_status=False,
                            ),
                        ],
                    ),
                    SupervisionTypeSpan(
                        start_date=revocation_period.admission_date,
                        end_date=None,
                        supervision_type=None,
                        start_critical_statuses=[
                            UsMoSentenceStatus(
                                sentence_external_id="123",
                                sentence_status_external_id="test-status-1",
                                status_date=revocation_period.admission_date,
                                status_code="50N1050",
                                status_description="Parole Viol Upd-Fel Law Viol",
                                person_external_id="1",
                                is_supervision_type_critical_status=False,
                                is_supervision_out_status=False,
                                is_supervision_in_status=False,
                                is_incarceration_in_status=True,
                                is_incarceration_out_status=False,
                                is_lifetime_supervision_start_status=False,
                                is_sentence_termination_status_candidate=False,
                                is_investigation_status=False,
                                is_sentence_termimination_status=False,
                            ),
                        ],
                        end_critical_statuses=[],
                    ),
                ],
            )
        )

        supervision_sentence = FakeUsMoSupervisionSentence.fake_sentence_from_sentence(
            StateSupervisionSentence.new_with_defaults(
                state_code="US_MO",
                supervision_sentence_id=123,
                status=StateSentenceStatus.PRESENT_WITHOUT_INFO,
                start_date=date(2008, 1, 1),
            ),
            supervision_type_spans=[
                SupervisionTypeSpan(
                    start_date=supervision_period.start_date,
                    end_date=temp_custody_period.admission_date,
                    supervision_type=StateSupervisionSentenceSupervisionType.PROBATION,
                    start_critical_statuses=[
                        UsMoSentenceStatus(
                            sentence_external_id="123",
                            sentence_status_external_id="test-status-1",
                            status_date=temp_custody_period.admission_date,
                            status_code="15I1000",
                            status_description="New Court Probation",
                            person_external_id="1",
                            is_supervision_type_critical_status=False,
                            is_supervision_out_status=False,
                            is_supervision_in_status=False,
                            is_incarceration_in_status=True,
                            is_incarceration_out_status=False,
                            is_lifetime_supervision_start_status=False,
                            is_sentence_termination_status_candidate=False,
                            is_investigation_status=False,
                            is_sentence_termimination_status=False,
                        ),
                    ],
                    end_critical_statuses=[
                        UsMoSentenceStatus(
                            sentence_external_id="123",
                            sentence_status_external_id="test-status-1",
                            status_date=temp_custody_period.admission_date,
                            status_code="65O2015",
                            status_description="Court Probation Suspension",
                            person_external_id="1",
                            is_supervision_type_critical_status=False,
                            is_supervision_out_status=False,
                            is_supervision_in_status=False,
                            is_incarceration_in_status=True,
                            is_incarceration_out_status=False,
                            is_lifetime_supervision_start_status=False,
                            is_sentence_termination_status_candidate=False,
                            is_investigation_status=False,
                            is_sentence_termimination_status=False,
                        ),
                    ],
                ),
                SupervisionTypeSpan(
                    start_date=temp_custody_period.admission_date,
                    end_date=revocation_period.admission_date,
                    supervision_type=None,
                    start_critical_statuses=[
                        UsMoSentenceStatus(
                            sentence_external_id="123",
                            sentence_status_external_id="test-status-1",
                            status_date=temp_custody_period.admission_date,
                            status_code="40I0050",
                            status_description="Board Holdover",
                            person_external_id="1",
                            is_supervision_type_critical_status=False,
                            is_supervision_out_status=False,
                            is_supervision_in_status=False,
                            is_incarceration_in_status=True,
                            is_incarceration_out_status=False,
                            is_lifetime_supervision_start_status=False,
                            is_sentence_termination_status_candidate=False,
                            is_investigation_status=False,
                            is_sentence_termimination_status=False,
                        ),
                    ],
                    end_critical_statuses=[
                        UsMoSentenceStatus(
                            sentence_external_id="123",
                            sentence_status_external_id="test-status-1",
                            status_date=revocation_period.admission_date,
                            status_code="45O2005",
                            status_description="Prob Rev-New Felony Conv",
                            person_external_id="1",
                            is_supervision_type_critical_status=False,
                            is_supervision_out_status=False,
                            is_supervision_in_status=False,
                            is_incarceration_in_status=True,
                            is_incarceration_out_status=False,
                            is_lifetime_supervision_start_status=False,
                            is_sentence_termination_status_candidate=False,
                            is_investigation_status=False,
                            is_sentence_termimination_status=False,
                        ),
                    ],
                ),
                SupervisionTypeSpan(
                    start_date=revocation_period.admission_date,
                    end_date=None,
                    supervision_type=None,
                    start_critical_statuses=[
                        UsMoSentenceStatus(
                            sentence_external_id="123",
                            sentence_status_external_id="test-status-1",
                            status_date=revocation_period.admission_date,
                            status_code="45O2005",
                            status_description="Prob Rev-New Felony Conv",
                            person_external_id="1",
                            is_supervision_type_critical_status=False,
                            is_supervision_out_status=False,
                            is_supervision_in_status=False,
                            is_incarceration_in_status=True,
                            is_incarceration_out_status=False,
                            is_lifetime_supervision_start_status=False,
                            is_sentence_termination_status_candidate=False,
                            is_investigation_status=False,
                            is_sentence_termimination_status=False,
                        ),
                    ],
                    end_critical_statuses=[],
                ),
            ],
        )

        incarceration_events = self._run_find_incarceration_events(
            state_code_override="US_MO",
            incarceration_periods=[temp_custody_period, revocation_period],
            incarceration_sentences=[incarceration_sentence],
            supervision_sentences=[supervision_sentence],
            supervision_periods=[supervision_period],
            supervision_period_to_agent_association=[
                {
                    "agent_id": 000,
                    "agent_external_id": None,
                    "supervision_period_id": supervision_period.supervision_period_id,
                    "agent_start_date": date(2008, 1, 1),
                    "agent_end_date": None,
                }
            ],
        )

        assert temp_custody_period.admission_reason is not None
        assert temp_custody_period.release_date is not None
        assert temp_custody_period.release_reason is not None
        assert revocation_period.release_date is not None
        assert revocation_period.admission_reason is not None
        assert revocation_period.release_reason is not None
        self.assertCountEqual(
            [
                IncarcerationStayEvent(
                    admission_reason=temp_custody_period.admission_reason,
                    admission_reason_raw_text=temp_custody_period.admission_reason_raw_text,
                    state_code=temp_custody_period.state_code,
                    event_date=temp_custody_period.admission_date,
                    facility=temp_custody_period.facility,
                    county_of_residence=_COUNTY_OF_RESIDENCE,
                    specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.PAROLE_BOARD_HOLD,
                ),
                IncarcerationStayEvent(
                    admission_reason=revocation_period.admission_reason,
                    admission_reason_raw_text=revocation_period.admission_reason_raw_text,
                    state_code=revocation_period.state_code,
                    event_date=revocation_period.admission_date,
                    facility=revocation_period.facility,
                    county_of_residence=_COUNTY_OF_RESIDENCE,
                    specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
                    commitment_from_supervision_supervision_type=StateSupervisionPeriodSupervisionType.DUAL,
                ),
                IncarcerationStandardAdmissionEvent(
                    state_code=temp_custody_period.state_code,
                    event_date=temp_custody_period.admission_date,
                    facility=temp_custody_period.facility,
                    county_of_residence=_COUNTY_OF_RESIDENCE,
                    admission_reason=temp_custody_period.admission_reason,
                    admission_reason_raw_text=temp_custody_period.admission_reason_raw_text,
                    specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.PAROLE_BOARD_HOLD,
                ),
                IncarcerationCommitmentFromSupervisionAdmissionEvent(
                    state_code=revocation_period.state_code,
                    event_date=revocation_period.admission_date,
                    facility=revocation_period.facility,
                    county_of_residence=_COUNTY_OF_RESIDENCE,
                    admission_reason=revocation_period.admission_reason,
                    admission_reason_raw_text=revocation_period.admission_reason_raw_text,
                    supervision_type=StateSupervisionPeriodSupervisionType.DUAL,
                    specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
                    case_type=StateSupervisionCaseType.GENERAL,
                    supervision_level=supervision_period.supervision_level,
                    assessment_score_bucket=DEFAULT_ASSESSMENT_SCORE_BUCKET,
                ),
                IncarcerationReleaseEvent(
                    state_code=temp_custody_period.state_code,
                    event_date=temp_custody_period.release_date,
                    facility=temp_custody_period.facility,
                    county_of_residence=_COUNTY_OF_RESIDENCE,
                    release_reason=temp_custody_period.release_reason,
                    admission_reason=StateIncarcerationPeriodAdmissionReason.TEMPORARY_CUSTODY,
                    total_days_incarcerated=(
                        temp_custody_period.release_date
                        - temp_custody_period.admission_date
                    ).days,
                    purpose_for_incarceration=StateSpecializedPurposeForIncarceration.PAROLE_BOARD_HOLD,
                ),
                IncarcerationReleaseEvent(
                    state_code=revocation_period.state_code,
                    event_date=revocation_period.release_date,
                    facility=revocation_period.facility,
                    county_of_residence=_COUNTY_OF_RESIDENCE,
                    release_reason=revocation_period.release_reason,
                    admission_reason=StateIncarcerationPeriodAdmissionReason.REVOCATION,
                    commitment_from_supervision_supervision_type=StateSupervisionPeriodSupervisionType.DUAL,
                    total_days_incarcerated=(
                        revocation_period.release_date
                        - revocation_period.admission_date
                    ).days,
                    purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
                ),
            ],
            incarceration_events,
        )

    def testFindIncarcerationEvents_usMo_tempCustody(self) -> None:
        """Tests that when there is only a temporary custody period."""

        temp_custody_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            external_id="1",
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_MO",
            facility="PRISON",
            admission_date=date(2008, 11, 20),
            admission_reason=StateIncarcerationPeriodAdmissionReason.TEMPORARY_CUSTODY,
            admission_reason_raw_text="40I0050",
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            specialized_purpose_for_incarceration_raw_text="S",
            release_date=date(2008, 11, 21),
            release_reason=StateIncarcerationPeriodReleaseReason.RELEASED_FROM_TEMPORARY_CUSTODY,
        )

        assert temp_custody_period.admission_date is not None
        assert temp_custody_period.admission_reason is not None
        assert temp_custody_period.release_date is not None
        assert temp_custody_period.release_reason is not None
        incarceration_sentence = FakeUsMoIncarcerationSentence.fake_sentence_from_sentence(
            StateIncarcerationSentence.new_with_defaults(
                state_code="US_MO",
                incarceration_sentence_id=123,
                status=StateSentenceStatus.PRESENT_WITHOUT_INFO,
                start_date=date(2008, 1, 1),
            ),
            supervision_type_spans=[
                SupervisionTypeSpan(
                    start_date=temp_custody_period.admission_date,
                    end_date=temp_custody_period.release_date,
                    supervision_type=StateSupervisionSentenceSupervisionType.PROBATION,
                    start_critical_statuses=[
                        UsMoSentenceStatus(
                            sentence_external_id="123",
                            sentence_status_external_id="test-status-1",
                            status_date=temp_custody_period.admission_date,
                            status_code="65O2015",
                            status_description="Court Probation Suspension",
                            person_external_id="1",
                            is_supervision_type_critical_status=False,
                            is_supervision_out_status=False,
                            is_supervision_in_status=False,
                            is_incarceration_in_status=True,
                            is_incarceration_out_status=False,
                            is_lifetime_supervision_start_status=False,
                            is_sentence_termination_status_candidate=False,
                            is_investigation_status=False,
                            is_sentence_termimination_status=False,
                        ),
                    ],
                    end_critical_statuses=[
                        UsMoSentenceStatus(
                            sentence_external_id="123",
                            sentence_status_external_id="test-status-2",
                            status_date=temp_custody_period.release_date,
                            status_code="65I2015",
                            status_description="Court Probation Reinstated",
                            person_external_id="1",
                            is_supervision_type_critical_status=False,
                            is_supervision_out_status=False,
                            is_supervision_in_status=False,
                            is_incarceration_in_status=True,
                            is_incarceration_out_status=False,
                            is_lifetime_supervision_start_status=False,
                            is_sentence_termination_status_candidate=False,
                            is_investigation_status=False,
                            is_sentence_termimination_status=False,
                        ),
                    ],
                ),
                SupervisionTypeSpan(
                    start_date=temp_custody_period.release_date,
                    end_date=None,
                    supervision_type=None,
                    start_critical_statuses=[],
                    end_critical_statuses=[],
                ),
            ],
        )

        supervision_sentence = FakeUsMoSupervisionSentence.fake_sentence_from_sentence(
            StateSupervisionSentence.new_with_defaults(
                state_code="US_MO",
                supervision_sentence_id=123,
                status=StateSentenceStatus.PRESENT_WITHOUT_INFO,
                start_date=date(2008, 1, 1),
            ),
            supervision_type_spans=[
                SupervisionTypeSpan(
                    start_date=temp_custody_period.admission_date,
                    end_date=temp_custody_period.release_date,
                    supervision_type=StateSupervisionSentenceSupervisionType.PROBATION,
                    start_critical_statuses=[
                        UsMoSentenceStatus(
                            sentence_external_id="123",
                            sentence_status_external_id="test-status-2",
                            status_date=temp_custody_period.admission_date,
                            status_code="65I2015",
                            status_description="Court Probation Suspension",
                            person_external_id="1",
                            is_supervision_type_critical_status=False,
                            is_supervision_out_status=False,
                            is_supervision_in_status=False,
                            is_incarceration_in_status=True,
                            is_incarceration_out_status=False,
                            is_lifetime_supervision_start_status=False,
                            is_sentence_termination_status_candidate=False,
                            is_investigation_status=False,
                            is_sentence_termimination_status=False,
                        ),
                    ],
                    end_critical_statuses=[
                        UsMoSentenceStatus(
                            sentence_external_id="123",
                            sentence_status_external_id="test-status-2",
                            status_date=temp_custody_period.release_date,
                            status_code="65I2015",
                            status_description="Court Probation Reinstated",
                            person_external_id="1",
                            is_supervision_type_critical_status=False,
                            is_supervision_out_status=False,
                            is_supervision_in_status=False,
                            is_incarceration_in_status=True,
                            is_incarceration_out_status=False,
                            is_lifetime_supervision_start_status=False,
                            is_sentence_termination_status_candidate=False,
                            is_investigation_status=False,
                            is_sentence_termimination_status=False,
                        ),
                    ],
                ),
                SupervisionTypeSpan(
                    start_date=temp_custody_period.release_date,
                    end_date=None,
                    supervision_type=None,
                    start_critical_statuses=[
                        UsMoSentenceStatus(
                            sentence_external_id="123",
                            sentence_status_external_id="test-status-2",
                            status_date=temp_custody_period.release_date,
                            status_code="40O9010",
                            status_description="Release to Probation",
                            person_external_id="1",
                            is_supervision_type_critical_status=False,
                            is_supervision_out_status=False,
                            is_supervision_in_status=False,
                            is_incarceration_in_status=True,
                            is_incarceration_out_status=False,
                            is_lifetime_supervision_start_status=False,
                            is_sentence_termination_status_candidate=False,
                            is_investigation_status=False,
                            is_sentence_termimination_status=False,
                        ),
                    ],
                    end_critical_statuses=[],
                ),
            ],
        )

        incarceration_events = self._run_find_incarceration_events(
            state_code_override="US_MO",
            incarceration_periods=[temp_custody_period],
            incarceration_sentences=[incarceration_sentence],
            supervision_sentences=[supervision_sentence],
        )

        self.assertCountEqual(
            [
                IncarcerationStayEvent(
                    admission_reason=temp_custody_period.admission_reason,
                    admission_reason_raw_text=temp_custody_period.admission_reason_raw_text,
                    state_code=temp_custody_period.state_code,
                    event_date=temp_custody_period.admission_date,
                    facility=temp_custody_period.facility,
                    county_of_residence=_COUNTY_OF_RESIDENCE,
                    specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.PAROLE_BOARD_HOLD,
                ),
                IncarcerationStandardAdmissionEvent(
                    state_code=temp_custody_period.state_code,
                    event_date=temp_custody_period.admission_date,
                    facility=temp_custody_period.facility,
                    county_of_residence=_COUNTY_OF_RESIDENCE,
                    admission_reason=temp_custody_period.admission_reason,
                    admission_reason_raw_text=temp_custody_period.admission_reason_raw_text,
                    specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.PAROLE_BOARD_HOLD,
                ),
                IncarcerationReleaseEvent(
                    state_code=temp_custody_period.state_code,
                    event_date=temp_custody_period.release_date,
                    facility=temp_custody_period.facility,
                    county_of_residence=_COUNTY_OF_RESIDENCE,
                    release_reason=temp_custody_period.release_reason,
                    admission_reason=StateIncarcerationPeriodAdmissionReason.TEMPORARY_CUSTODY,
                    purpose_for_incarceration=StateSpecializedPurposeForIncarceration.PAROLE_BOARD_HOLD,
                    total_days_incarcerated=(
                        temp_custody_period.release_date
                        - temp_custody_period.admission_date
                    ).days,
                ),
            ],
            incarceration_events,
        )

    def testFindIncarcerationEvents_usId_RevocationAdmission(self) -> None:
        """Tests the find_incarceration_events function for state code US_ID."""

        supervision_period = StateSupervisionPeriod.new_with_defaults(
            supervision_period_id=_DEFAULT_SP_ID,
            external_id="sp1",
            state_code="US_ID",
            custodial_authority_raw_text="US_ID_DOC",
            start_date=date(2017, 3, 5),
            termination_date=date(2017, 5, 9),
            supervision_type=StateSupervisionPeriodSupervisionType.PROBATION,
            supervision_level=StateSupervisionLevel.MEDIUM,
            supervision_level_raw_text="MEDIUM",
            supervision_site="X|Y",
        )

        revocation_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=222,
            external_id="ip2",
            state_code="US_ID",
            custodial_authority_raw_text="US_ID_DOC",
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            admission_date=date(2017, 5, 17),
            admission_reason=StateIncarcerationPeriodAdmissionReason.ADMITTED_FROM_SUPERVISION,
            release_date=date(2017, 5, 18),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )

        supervision_sentence = StateSupervisionSentence.new_with_defaults(
            state_code="US_ID",
            supervision_sentence_id=111,
            start_date=date(2017, 1, 1),
            status=StateSentenceStatus.COMPLETED,
        )

        incarceration_events = self._run_find_incarceration_events(
            state_code_override="US_ID",
            incarceration_periods=[revocation_period],
            supervision_sentences=[supervision_sentence],
            supervision_periods=[supervision_period],
        )

        assert revocation_period.admission_date is not None
        assert revocation_period.release_date is not None
        assert revocation_period.release_reason is not None
        self.assertCountEqual(
            [
                IncarcerationStayEvent(
                    admission_reason=StateIncarcerationPeriodAdmissionReason.REVOCATION,
                    admission_reason_raw_text=revocation_period.admission_reason_raw_text,
                    state_code=revocation_period.state_code,
                    event_date=revocation_period.admission_date,
                    facility=revocation_period.facility,
                    county_of_residence=_COUNTY_OF_RESIDENCE,
                    specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
                    commitment_from_supervision_supervision_type=StateSupervisionPeriodSupervisionType.PROBATION,
                ),
                IncarcerationCommitmentFromSupervisionAdmissionEvent(
                    state_code=revocation_period.state_code,
                    event_date=revocation_period.admission_date,
                    facility=revocation_period.facility,
                    county_of_residence=_COUNTY_OF_RESIDENCE,
                    admission_reason=StateIncarcerationPeriodAdmissionReason.REVOCATION,
                    admission_reason_raw_text=revocation_period.admission_reason_raw_text,
                    supervision_type=supervision_period.supervision_type,
                    supervision_level=supervision_period.supervision_level,
                    supervision_level_raw_text=supervision_period.supervision_level_raw_text,
                    case_type=StateSupervisionCaseType.GENERAL,
                    specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
                    supervising_district_external_id="X",
                    level_1_supervision_location_external_id="Y",
                    level_2_supervision_location_external_id="X",
                    supervising_officer_external_id="XXX",
                    assessment_score_bucket=DEFAULT_ASSESSMENT_SCORE_BUCKET,
                ),
                IncarcerationReleaseEvent(
                    state_code=revocation_period.state_code,
                    event_date=revocation_period.release_date,
                    facility=revocation_period.facility,
                    county_of_residence=_COUNTY_OF_RESIDENCE,
                    release_reason=revocation_period.release_reason,
                    release_reason_raw_text=revocation_period.release_reason_raw_text,
                    admission_reason=StateIncarcerationPeriodAdmissionReason.REVOCATION,
                    commitment_from_supervision_supervision_type=StateSupervisionPeriodSupervisionType.PROBATION,
                    total_days_incarcerated=(
                        revocation_period.release_date
                        - revocation_period.admission_date
                    ).days,
                    purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
                ),
            ],
            incarceration_events,
        )

    def testFindIncarcerationEvents_usId_FailedTreatmentStatusChange(
        self,
    ) -> None:
        """Tests that with state code US_ID, treatment in prison periods that are
        followed by a transfer to general result in an admission event for the
        general period with the admission_reason STATUS_CHANGE.
        """
        treatment_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            external_id="1",
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_ID",
            facility="PRISON",
            admission_date=date(2008, 11, 20),
            admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.TREATMENT_IN_PRISON,
            release_date=date(2008, 12, 20),
            release_reason=StateIncarcerationPeriodReleaseReason.TRANSFER,
        )

        general_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1112,
            external_id="2",
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_ID",
            facility="PRISON",
            admission_date=date(2008, 12, 20),
            admission_reason=StateIncarcerationPeriodAdmissionReason.TRANSFER,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            release_date=date(2008, 12, 21),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
        )

        supervision_sentence = StateSupervisionSentence.new_with_defaults(
            state_code="US_ID",
            supervision_sentence_id=111,
            start_date=date(2017, 1, 1),
            status=StateSentenceStatus.COMPLETED,
        )

        incarceration_events = self._run_find_incarceration_events(
            state_code_override="US_ID",
            incarceration_periods=[treatment_period, general_period],
            supervision_sentences=[supervision_sentence],
        )

        assert treatment_period.admission_date is not None
        assert treatment_period.release_date is not None
        assert general_period.admission_date is not None
        assert general_period.release_date is not None
        assert general_period.release_reason is not None
        expected_events = [
            *expected_incarceration_stay_events(treatment_period),
            *expected_incarceration_stay_events(
                general_period,
                original_admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            ),
            IncarcerationStandardAdmissionEvent(
                state_code=treatment_period.state_code,
                event_date=treatment_period.admission_date,
                facility=treatment_period.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
                specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.TREATMENT_IN_PRISON,
            ),
            IncarcerationReleaseEvent(
                state_code=treatment_period.state_code,
                event_date=treatment_period.release_date,
                facility=treatment_period.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                release_reason=StateIncarcerationPeriodReleaseReason.STATUS_CHANGE,
                release_reason_raw_text=treatment_period.release_reason_raw_text,
                admission_reason=treatment_period.admission_reason,
                total_days_incarcerated=(
                    treatment_period.release_date - treatment_period.admission_date
                ).days,
                purpose_for_incarceration=StateSpecializedPurposeForIncarceration.TREATMENT_IN_PRISON,
            ),
            IncarcerationStandardAdmissionEvent(
                state_code=general_period.state_code,
                event_date=general_period.admission_date,
                facility=general_period.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                admission_reason=StateIncarcerationPeriodAdmissionReason.STATUS_CHANGE,
                specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            ),
            IncarcerationReleaseEvent(
                state_code=general_period.state_code,
                event_date=general_period.release_date,
                facility=general_period.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                release_reason=general_period.release_reason,
                release_reason_raw_text=general_period.release_reason_raw_text,
                admission_reason=treatment_period.admission_reason,
                total_days_incarcerated=(
                    general_period.release_date - general_period.admission_date
                ).days,
                purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            ),
        ]

        self.assertCountEqual(expected_events, incarceration_events)

    def testFindIncarcerationEvents_usPA_SanctionAdmission(self) -> None:
        """Tests the find_incarceration_events function for periods in US_PA, where
        there is a sanction admission for shock incarceration."""

        state_code = "US_PA"

        supervision_period = StateSupervisionPeriod.new_with_defaults(
            supervision_period_id=_DEFAULT_SP_ID,
            external_id="sp1",
            case_type_entries=[
                StateSupervisionCaseTypeEntry.new_with_defaults(
                    state_code=state_code, case_type=StateSupervisionCaseType.GENERAL
                )
            ],
            state_code=state_code,
            supervision_site="DISTRICT_1|OFFICE_2|456",
            start_date=date(2018, 3, 5),
            termination_date=date(2018, 5, 19),
            termination_reason=StateSupervisionPeriodTerminationReason.DISCHARGE,
            supervision_type=StateSupervisionPeriodSupervisionType.PAROLE,
            supervision_level=StateSupervisionLevel.MINIMUM,
            supervision_level_raw_text="LOW",
        )

        assessment = StateAssessment.new_with_defaults(
            state_code=state_code,
            assessment_type=StateAssessmentType.LSIR,
            assessment_level=StateAssessmentLevel.HIGH,
            assessment_score=33,
            assessment_date=date(2018, 3, 1),
        )

        parole_board_decision_entry = (
            StateSupervisionViolationResponseDecisionEntry.new_with_defaults(
                state_code=state_code,
                decision_raw_text=SHOCK_INCARCERATION_9_MONTHS,
                decision=StateSupervisionViolationResponseDecision.SHOCK_INCARCERATION,
            )
        )

        parole_board_permanent_decision = StateSupervisionViolationResponse.new_with_defaults(
            state_code=state_code,
            response_date=date(year=2018, month=5, day=16),
            response_type=StateSupervisionViolationResponseType.PERMANENT_DECISION,
            response_type_raw_text="PERMANENT_DECISION",
            deciding_body_type=StateSupervisionViolationResponseDecidingBodyType.PAROLE_BOARD,
            deciding_body_type_raw_text="PAROLE_BOARD",
            supervision_violation_response_decisions=[parole_board_decision_entry],
        )

        parole_board_hold = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=111,
            external_id="ip1",
            state_code=state_code,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            admission_date=date(2018, 3, 11),
            admission_reason=StateIncarcerationPeriodAdmissionReason.ADMITTED_FROM_SUPERVISION,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.PAROLE_BOARD_HOLD,
            release_date=date(2018, 5, 19),
            release_reason=StateIncarcerationPeriodReleaseReason.TRANSFER,
        )

        shock_incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=222,
            external_id="ip2",
            state_code=state_code,
            incarceration_type=StateIncarcerationType.COUNTY_JAIL,
            admission_date=date(2018, 5, 19),
            admission_reason=StateIncarcerationPeriodAdmissionReason.REVOCATION,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.SHOCK_INCARCERATION,
            # Program 46 indicates a revocation for a 6, 9 or 12 month stay
            specialized_purpose_for_incarceration_raw_text="CCIS-46",
            release_date=date(2019, 3, 3),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
        )

        assessments = [assessment]
        violation_responses = [parole_board_permanent_decision]

        incarceration_events = self._run_find_incarceration_events(
            state_code_override=state_code,
            incarceration_periods=[parole_board_hold, shock_incarceration_period],
            supervision_periods=[supervision_period],
            assessments=assessments,
            violation_responses=violation_responses,
            supervision_period_to_agent_association=_DEFAULT_SUPERVISION_PERIOD_AGENT_ASSOCIATION_LIST,
        )

        expected_board_hold_stay_events = expected_incarceration_stay_events(
            incarceration_period=parole_board_hold,
            original_admission_reason=StateIncarcerationPeriodAdmissionReason.TEMPORARY_CUSTODY,
        )

        expected_shock_stay_events = expected_incarceration_stay_events(
            incarceration_period=shock_incarceration_period,
            original_admission_reason=StateIncarcerationPeriodAdmissionReason.SANCTION_ADMISSION,
            commitment_from_supervision_supervision_type=StateSupervisionPeriodSupervisionType.PAROLE,
        )

        assert parole_board_hold.admission_date is not None
        assert shock_incarceration_period.admission_date is not None
        expected_admission_events = [
            IncarcerationStandardAdmissionEvent(
                state_code=state_code,
                event_date=parole_board_hold.admission_date,
                facility=parole_board_hold.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                admission_reason=StateIncarcerationPeriodAdmissionReason.TEMPORARY_CUSTODY,
                specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.PAROLE_BOARD_HOLD,
            ),
            IncarcerationCommitmentFromSupervisionAdmissionEvent(
                state_code=state_code,
                event_date=shock_incarceration_period.admission_date,
                facility=shock_incarceration_period.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                admission_reason=StateIncarcerationPeriodAdmissionReason.SANCTION_ADMISSION,
                admission_reason_raw_text=shock_incarceration_period.admission_reason_raw_text,
                supervision_type=supervision_period.supervision_type,
                supervision_level=supervision_period.supervision_level,
                supervision_level_raw_text=supervision_period.supervision_level_raw_text,
                case_type=StateSupervisionCaseType.GENERAL,
                specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.SHOCK_INCARCERATION,
                purpose_for_incarceration_subtype=SHOCK_INCARCERATION_9_MONTHS,
                supervising_district_external_id="DISTRICT_1",
                level_1_supervision_location_external_id="OFFICE_2",
                level_2_supervision_location_external_id="DISTRICT_1",
                supervising_officer_external_id="XXX",
                assessment_score=assessment.assessment_score,
                assessment_level=StateAssessmentLevel.HIGH,
                assessment_type=assessment.assessment_type,
                assessment_score_bucket=StateAssessmentLevel.HIGH.value,
            ),
        ]

        assert parole_board_hold.release_date is not None
        assert shock_incarceration_period.release_date is not None
        assert shock_incarceration_period.release_reason is not None
        expected_release_events = [
            IncarcerationReleaseEvent(
                state_code=state_code,
                event_date=parole_board_hold.release_date,
                facility=parole_board_hold.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                release_reason=StateIncarcerationPeriodReleaseReason.RELEASED_FROM_TEMPORARY_CUSTODY,
                release_reason_raw_text=parole_board_hold.release_reason_raw_text,
                admission_reason=StateIncarcerationPeriodAdmissionReason.TEMPORARY_CUSTODY,
                total_days_incarcerated=(
                    parole_board_hold.release_date - parole_board_hold.admission_date
                ).days,
                purpose_for_incarceration=StateSpecializedPurposeForIncarceration.PAROLE_BOARD_HOLD,
            ),
            IncarcerationReleaseEvent(
                state_code=state_code,
                event_date=shock_incarceration_period.release_date,
                facility=shock_incarceration_period.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                release_reason=shock_incarceration_period.release_reason,
                release_reason_raw_text=shock_incarceration_period.release_reason_raw_text,
                admission_reason=StateIncarcerationPeriodAdmissionReason.SANCTION_ADMISSION,
                commitment_from_supervision_supervision_type=StateSupervisionPeriodSupervisionType.PAROLE,
                total_days_incarcerated=(
                    shock_incarceration_period.release_date
                    - shock_incarceration_period.admission_date
                ).days,
                purpose_for_incarceration=StateSpecializedPurposeForIncarceration.SHOCK_INCARCERATION,
            ),
        ]

        self.assertCountEqual(
            [
                *expected_board_hold_stay_events,
                *expected_shock_stay_events,
                *expected_admission_events,
                *expected_release_events,
            ],
            incarceration_events,
        )


class TestFindIncarcerationStays(unittest.TestCase):
    """Tests the find_incarceration_stays function."""

    def setUp(self) -> None:
        self.identifier = identifier.IncarcerationIdentifier()

    def _run_find_incarceration_stays_with_no_sentences(
        self,
        incarceration_period: StateIncarcerationPeriod,
        county_of_residence: Optional[str] = _COUNTY_OF_RESIDENCE,
        incarceration_period_judicial_district_association: Optional[
            Dict[int, Dict[str, Any]]
        ] = None,
        incarceration_delegate: Optional[StateSpecificIncarcerationDelegate] = None,
    ) -> List[IncarcerationStayEvent]:
        """Runs `find_incarceration_stays` without providing sentence information.
        Sentence information is only used in `US_MO` to inform information about
        supervision types prior to admission. All tests using this method should not
        require that state specific logic.
        """
        incarceration_period_judicial_district_association = incarceration_period_judicial_district_association or {
            _DEFAULT_IP_ID: _DEFAULT_INCARCERATION_PERIOD_JUDICIAL_DISTRICT_ASSOCIATION[
                0
            ]
        }

        incarceration_delegate = incarceration_delegate or UsXxIncarcerationDelegate()

        incarceration_period_index = default_normalized_ip_index_for_tests(
            incarceration_periods=[incarceration_period]
        )

        # pylint: disable=protected-access
        return self.identifier._find_incarceration_stays(
            incarceration_period,
            incarceration_period_index,
            incarceration_period_judicial_district_association,
            incarceration_delegate,
            {},  # commitments from supervision
            county_of_residence,
        )

    def test_find_incarceration_stays_type_us_mo(self) -> None:
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_MO",
            facility="PRISON3",
            admission_date=date(2010, 1, 20),
            admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            release_date=date(2010, 3, 1),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )

        assert incarceration_period.incarceration_period_id is not None
        incarceration_period_judicial_district_association = {
            incarceration_period.incarceration_period_id: {
                "incarceration_period_id": incarceration_period.incarceration_period_id,
                "judicial_district_code": "XXX",
            }
        }

        incarceration_events = self._run_find_incarceration_stays_with_no_sentences(
            incarceration_period,
            incarceration_period_judicial_district_association=incarceration_period_judicial_district_association,
        )

        expected_incarceration_events = expected_incarceration_stay_events(
            incarceration_period
        )

        updated_expected_events = []
        for expected_event in expected_incarceration_events:
            updated_expected_events.append(
                attr.evolve(
                    expected_event,
                    judicial_district_code="XXX",
                )
            )

        self.assertEqual(updated_expected_events, incarceration_events)

    def test_find_incarceration_stays(self) -> None:
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            facility="PRISON3",
            admission_date=date(2000, 1, 20),
            admission_reason=StateIncarcerationPeriodAdmissionReason.REVOCATION,
            release_date=date(2010, 12, 1),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )

        incarceration_events = self._run_find_incarceration_stays_with_no_sentences(
            incarceration_period, _COUNTY_OF_RESIDENCE
        )

        expected_incarceration_events = expected_incarceration_stay_events(
            incarceration_period
        )

        self.assertEqual(expected_incarceration_events, incarceration_events)

    @freeze_time("2019-11-01")
    def test_find_incarceration_stays_no_release(self) -> None:
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            facility="PRISON3",
            admission_date=date(2018, 1, 20),
            admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )

        incarceration_events = self._run_find_incarceration_stays_with_no_sentences(
            incarceration_period, _COUNTY_OF_RESIDENCE
        )

        expected_incarceration_events = expected_incarceration_stay_events(
            incarceration_period
        )

        self.assertEqual(expected_incarceration_events, incarceration_events)

    def test_find_incarceration_stays_no_admission_or_release(self) -> None:
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            facility="PRISON3",
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )

        with self.assertRaises(ValueError):
            _ = self._run_find_incarceration_stays_with_no_sentences(
                incarceration_period, _COUNTY_OF_RESIDENCE
            )

    def test_find_incarceration_stays_no_release_reason(self) -> None:
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            facility="PRISON3",
            admission_date=date(2000, 1, 20),
            admission_reason=StateIncarcerationPeriodAdmissionReason.REVOCATION,
            release_date=date(2010, 12, 1),
            release_reason=None,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )

        incarceration_events = self._run_find_incarceration_stays_with_no_sentences(
            incarceration_period, _COUNTY_OF_RESIDENCE
        )

        expected_incarceration_events = expected_incarceration_stay_events(
            incarceration_period
        )

        self.assertEqual(expected_incarceration_events, incarceration_events)

    def test_find_incarceration_stays_admitted_end_of_month(self) -> None:
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            facility="PRISON3",
            admission_date=date(2000, 1, 31),
            admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            release_date=date(2000, 2, 13),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )

        incarceration_events = self._run_find_incarceration_stays_with_no_sentences(
            incarceration_period, _COUNTY_OF_RESIDENCE
        )

        expected_incarceration_events = expected_incarceration_stay_events(
            incarceration_period
        )

        self.assertEqual(expected_incarceration_events, incarceration_events)

    @freeze_time("2019-12-02")
    def test_find_incarceration_stays_still_in_custody(self) -> None:
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            facility="PRISON3",
            admission_date=date(2019, 11, 30),
            admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )

        incarceration_events = self._run_find_incarceration_stays_with_no_sentences(
            incarceration_period, _COUNTY_OF_RESIDENCE
        )

        expected_incarceration_events = expected_incarceration_stay_events(
            incarceration_period
        )

        self.assertEqual(expected_incarceration_events, incarceration_events)

    def test_find_incarceration_stays_released_end_of_month(self) -> None:
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            facility="PRISON3",
            admission_date=date(2019, 11, 29),
            admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            release_date=date(2019, 11, 30),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )

        incarceration_events = self._run_find_incarceration_stays_with_no_sentences(
            incarceration_period, _COUNTY_OF_RESIDENCE
        )

        # We do not count the termination date of an incarceration period as a day the person is incarcerated.
        expected_incarceration_events = expected_incarceration_stay_events(
            incarceration_period
        )

        self.assertEqual(expected_incarceration_events, incarceration_events)

    def test_find_incarceration_stays_transfers_end_of_month(self) -> None:
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            facility="PRISON3",
            admission_date=date(2019, 11, 29),
            admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            release_date=date(2019, 11, 30),
            release_reason=StateIncarcerationPeriodReleaseReason.TRANSFER,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )
        incarceration_period_2 = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            facility="PRISON4",
            admission_date=date(2019, 11, 30),
            admission_reason=StateIncarcerationPeriodAdmissionReason.TRANSFER,
            release_date=date(2019, 12, 1),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )

        incarceration_events_period_1 = (
            self._run_find_incarceration_stays_with_no_sentences(
                incarceration_period, _COUNTY_OF_RESIDENCE
            )
        )

        expected_incarceration_events = expected_incarceration_stay_events(
            incarceration_period
        )

        self.assertEqual(expected_incarceration_events, incarceration_events_period_1)

        incarceration_events_period_2 = (
            self._run_find_incarceration_stays_with_no_sentences(
                incarceration_period_2, _COUNTY_OF_RESIDENCE
            )
        )

        expected_incarceration_events = expected_incarceration_stay_events(
            incarceration_period_2
        )

        self.assertEqual(expected_incarceration_events, incarceration_events_period_2)

    def test_find_incarceration_stays_released_first_of_month(self) -> None:
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            facility="PRISON3",
            admission_date=date(2019, 11, 15),
            admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            release_date=date(2019, 12, 1),
            release_reason=StateIncarcerationPeriodReleaseReason.TRANSFER,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )

        incarceration_events = self._run_find_incarceration_stays_with_no_sentences(
            incarceration_period, _COUNTY_OF_RESIDENCE
        )

        expected_incarceration_events = expected_incarceration_stay_events(
            incarceration_period
        )

        self.assertEqual(expected_incarceration_events, incarceration_events)

    def test_find_incarceration_stays_only_one_day(self) -> None:
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            facility="PRISON3",
            admission_date=date(2019, 7, 31),
            admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            release_date=date(2019, 7, 31),
            release_reason=StateIncarcerationPeriodReleaseReason.TRANSFER,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )

        incarceration_events = self._run_find_incarceration_stays_with_no_sentences(
            incarceration_period, _COUNTY_OF_RESIDENCE
        )

        # We do not count people who were released on the last day of the month as being incarcerated on that last day.
        # In normal circumstances, if this person remained incarcerated but had a quick, one-day transfer, there will
        # be another incarceration period that opens on the last day of the month with a later termination date - we
        # *will* count this one.
        expected_incarceration_events = expected_incarceration_stay_events(
            incarceration_period
        )

        self.assertEqual(expected_incarceration_events, incarceration_events)

    def test_find_incarceration_stays_county_jail(self) -> None:
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            incarceration_type=StateIncarcerationType.COUNTY_JAIL,
            state_code="US_XX",
            facility="PRISON3",
            admission_date=date(2000, 1, 31),
            admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            release_date=date(2000, 2, 13),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )

        incarceration_events = self._run_find_incarceration_stays_with_no_sentences(
            incarceration_period, _COUNTY_OF_RESIDENCE
        )

        expected_incarceration_events = expected_incarceration_stay_events(
            incarceration_period
        )

        self.assertEqual(expected_incarceration_events, incarceration_events)

    def test_find_incarceration_stays_original_admission_reason(self) -> None:
        incarceration_period_1 = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            facility="PRISON3",
            admission_date=date(2010, 1, 20),
            admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            release_date=date(2010, 3, 1),
            release_reason=StateIncarcerationPeriodReleaseReason.TRANSFER,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )

        incarceration_period_2 = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=2222,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            facility="PRISON3",
            admission_date=date(2010, 3, 1),
            admission_reason=StateIncarcerationPeriodAdmissionReason.TRANSFER,
            release_date=date(2010, 3, 31),
            release_reason=StateIncarcerationPeriodReleaseReason.TRANSFER,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )

        assert incarceration_period_1.incarceration_period_id is not None
        incarceration_period_judicial_district_association = {
            incarceration_period_1.incarceration_period_id: {
                "incarceration_period_id": incarceration_period_1.incarceration_period_id,
                "judicial_district_code": "XXX",
            }
        }

        ips = [incarceration_period_1, incarceration_period_2]

        incarceration_period_index = default_normalized_ip_index_for_tests(
            incarceration_periods=ips
        )

        incarceration_delegate = UsXxIncarcerationDelegate()

        # pylint: disable=protected-access
        incarceration_events = self.identifier._find_incarceration_stays(
            incarceration_period_2,
            incarceration_period_index,
            incarceration_period_judicial_district_association,
            incarceration_delegate,
            {},  # commitments from supervision
            _COUNTY_OF_RESIDENCE,
        )

        expected_incarceration_events = expected_incarceration_stay_events(
            incarceration_period_2,
            original_admission_reason=incarceration_period_1.admission_reason,
            original_admission_reason_raw_text=incarceration_period_1.admission_reason_raw_text,
        )

        self.assertEqual(expected_incarceration_events, incarceration_events)

    def test_find_incarceration_stays_two_official_admission_reasons(self) -> None:
        incarceration_period_1 = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            facility="PRISON3",
            admission_date=date(2010, 1, 20),
            admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            release_date=date(2010, 3, 1),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )

        incarceration_period_2 = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=2222,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            facility="PRISON3",
            admission_date=date(2010, 3, 1),
            admission_reason=StateIncarcerationPeriodAdmissionReason.REVOCATION,
            release_date=date(2010, 3, 31),
            release_reason=StateIncarcerationPeriodReleaseReason.TRANSFER,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )

        assert incarceration_period_1.incarceration_period_id is not None
        incarceration_period_judicial_district_association = {
            incarceration_period_1.incarceration_period_id: {
                "incarceration_period_id": incarceration_period_1.incarceration_period_id,
                "judicial_district_code": "XXX",
            }
        }

        incarceration_periods = [incarceration_period_1, incarceration_period_2]

        incarceration_period_index = default_normalized_ip_index_for_tests(
            incarceration_periods=incarceration_periods
        )

        # pylint: disable=protected-access
        incarceration_events = self.identifier._find_incarceration_stays(
            incarceration_period_2,
            incarceration_period_index,
            incarceration_period_judicial_district_association,
            incarceration_period_index.incarceration_delegate,
            {},  # commitments from supervision
            _COUNTY_OF_RESIDENCE,
        )

        expected_incarceration_events = expected_incarceration_stay_events(
            incarceration_period_2
        )

        self.assertEqual(expected_incarceration_events, incarceration_events)


class TestAdmissionEventForPeriod(unittest.TestCase):
    """Tests the admission_event_for_period function."""

    def setUp(self) -> None:
        self.identifier = identifier.IncarcerationIdentifier()

    def _run_admission_event_for_period(
        self,
        incarceration_period: StateIncarcerationPeriod,
        incarceration_period_index: Optional[NormalizedIncarcerationPeriodIndex] = None,
        incarceration_sentences: Optional[List[StateIncarcerationSentence]] = None,
        supervision_sentences: Optional[List[StateSupervisionSentence]] = None,
        supervision_periods: Optional[List[StateSupervisionPeriod]] = None,
        assessments: Optional[List[StateAssessment]] = None,
        violation_responses: Optional[List[StateSupervisionViolationResponse]] = None,
        state_specific_override: Optional[str] = None,
        county_of_residence: Optional[str] = _COUNTY_OF_RESIDENCE,
    ) -> Optional[IncarcerationAdmissionEvent]:
        """Runs `admission_event_for_period` without providing sentence information.
        Sentence information is only used in `US_MO` to inform information about
        supervision types prior to admission. All tests using this method should not
        require that state specific logic.
        """
        incarceration_sentences = incarceration_sentences or []
        supervision_sentences = supervision_sentences or []
        state_specific_delegates = (
            get_all_state_specific_delegates(state_code=state_specific_override)
            if state_specific_override
            else STATE_DELEGATES_FOR_TESTS
        )

        incarceration_period_index = (
            incarceration_period_index
            or default_normalized_ip_index_for_tests(
                incarceration_periods=[incarceration_period]
            )
        )
        supervision_period_index = default_normalized_sp_index_for_tests(
            supervision_periods=supervision_periods
        )
        assessments = assessments or []
        sorted_violation_responses = (
            sorted(violation_responses, key=lambda b: b.response_date or date.min)
            if violation_responses
            else []
        )

        # pylint: disable=protected-access
        return self.identifier._admission_event_for_period(
            incarceration_delegate=state_specific_delegates.incarceration_delegate,
            commitment_from_supervision_delegate=state_specific_delegates.commitment_from_supervision_delegate,
            violation_delegate=state_specific_delegates.violation_delegate,
            supervision_delegate=state_specific_delegates.supervision_delegate,
            incarceration_sentences=incarceration_sentences,
            supervision_sentences=supervision_sentences,
            incarceration_period=incarceration_period,
            incarceration_period_index=incarceration_period_index,
            supervision_period_index=supervision_period_index,
            assessments=assessments,
            sorted_violation_responses=sorted_violation_responses,
            supervision_period_to_agent_associations=_DEFAULT_SUPERVISION_PERIOD_AGENT_ASSOCIATIONS,
            county_of_residence=county_of_residence,
        )

    def test_admission_event_for_period_us_mo(self) -> None:
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_MO",
            facility="PRISON3",
            admission_date=date(2010, 1, 20),
            admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            release_date=date(2010, 3, 1),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )
        supervision_period = StateSupervisionPeriod.new_with_defaults(
            supervision_period_id=1111,
            state_code="US_MO",
            start_date=date(2010, 1, 1),
            termination_date=date(2010, 2, 15),
        )
        supervision_sentence = FakeUsMoSupervisionSentence.fake_sentence_from_sentence(
            StateSupervisionSentence.new_with_defaults(
                supervision_sentence_id=1111,
                state_code="US_MO",
                supervision_type=StateSupervisionSentenceSupervisionType.PROBATION,
                start_date=date(2010, 1, 1),
                status=StateSentenceStatus.PRESENT_WITHOUT_INFO,
            ),
            supervision_type_spans=[
                SupervisionTypeSpan(
                    start_date=date(2010, 1, 1),
                    end_date=None,
                    supervision_type=StateSupervisionSentenceSupervisionType.PROBATION,
                    start_critical_statuses=[
                        UsMoSentenceStatus(
                            sentence_external_id="123",
                            sentence_status_external_id="test-status-1",
                            status_date=date(2010, 1, 1),
                            status_code="40I2000",
                            status_description="Prob Rev-Technical",
                            person_external_id="1",
                            is_supervision_type_critical_status=False,
                            is_supervision_out_status=False,
                            is_supervision_in_status=False,
                            is_incarceration_in_status=False,
                            is_incarceration_out_status=False,
                            is_lifetime_supervision_start_status=False,
                            is_sentence_termination_status_candidate=False,
                            is_investigation_status=False,
                            is_sentence_termimination_status=False,
                        )
                    ],
                    end_critical_statuses=[],
                )
            ],
        )

        admission_event = self._run_admission_event_for_period(
            incarceration_period=incarceration_period,
            supervision_periods=[supervision_period],
            supervision_sentences=[supervision_sentence],
        )

        assert incarceration_period.admission_date is not None
        assert incarceration_period.admission_reason is not None
        self.assertEqual(
            IncarcerationStandardAdmissionEvent(
                state_code=incarceration_period.state_code,
                event_date=incarceration_period.admission_date,
                facility="PRISON3",
                county_of_residence=_COUNTY_OF_RESIDENCE,
                admission_reason=incarceration_period.admission_reason,
                specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            ),
            admission_event,
        )

    def test_admission_event_for_period(self) -> None:
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            facility="PRISON3",
            admission_date=date(2008, 11, 20),
            admission_reason=StateIncarcerationPeriodAdmissionReason.REVOCATION,
            release_date=date(2010, 12, 4),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )

        admission_event = self._run_admission_event_for_period(
            incarceration_period=incarceration_period,
        )

        assert incarceration_period.admission_date is not None
        assert incarceration_period.admission_reason is not None
        self.assertEqual(
            IncarcerationCommitmentFromSupervisionAdmissionEvent(
                state_code=incarceration_period.state_code,
                event_date=incarceration_period.admission_date,
                facility="PRISON3",
                county_of_residence=_COUNTY_OF_RESIDENCE,
                admission_reason=incarceration_period.admission_reason,
                supervision_type=StateSupervisionPeriodSupervisionType.INTERNAL_UNKNOWN,
                specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
                case_type=StateSupervisionCaseType.GENERAL,
                assessment_score_bucket=DEFAULT_ASSESSMENT_SCORE_BUCKET,
            ),
            admission_event,
        )

    def test_admission_event_for_period_all_admission_reasons(self) -> None:
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            facility="PRISON3",
            admission_date=date(2013, 11, 20),
            release_date=date(2019, 12, 4),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )

        for admission_reason in StateIncarcerationPeriodAdmissionReason:
            incarceration_period.admission_reason = admission_reason

            # ADMITTED_FROM_SUPERVISION is an ingest-only enum
            if (
                admission_reason
                != StateIncarcerationPeriodAdmissionReason.ADMITTED_FROM_SUPERVISION
            ):
                admission_event = self._run_admission_event_for_period(
                    incarceration_period=incarceration_period,
                )

                self.assertIsNotNone(admission_event)

    def test_admission_event_for_period_specialized_pfi(self) -> None:
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            facility="PRISON3",
            admission_date=date(2008, 11, 20),
            admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.TREATMENT_IN_PRISON,
            release_date=date(2010, 12, 4),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
        )

        admission_event = self._run_admission_event_for_period(
            incarceration_period=incarceration_period,
        )

        assert incarceration_period.admission_date is not None
        assert incarceration_period.admission_reason is not None
        self.assertEqual(
            IncarcerationStandardAdmissionEvent(
                state_code=incarceration_period.state_code,
                event_date=incarceration_period.admission_date,
                facility="PRISON3",
                county_of_residence=_COUNTY_OF_RESIDENCE,
                admission_reason=incarceration_period.admission_reason,
                specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.TREATMENT_IN_PRISON,
            ),
            admission_event,
        )

    def test_admission_event_for_period_county_jail(self) -> None:
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            incarceration_type=StateIncarcerationType.COUNTY_JAIL,
            state_code="US_XX",
            facility="CJ10",
            admission_date=date(2013, 11, 20),
            admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            release_date=date(2019, 12, 4),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )

        admission_event = self._run_admission_event_for_period(
            incarceration_period=incarceration_period,
        )

        assert incarceration_period.admission_date is not None
        assert incarceration_period.admission_reason is not None
        self.assertEqual(
            IncarcerationStandardAdmissionEvent(
                state_code=incarceration_period.state_code,
                event_date=incarceration_period.admission_date,
                facility="CJ10",
                county_of_residence=_COUNTY_OF_RESIDENCE,
                admission_reason=incarceration_period.admission_reason,
                specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            ),
            admission_event,
        )

    def test_cannot_instantiate_IncarcerationAdmissionEvent(self) -> None:
        """Test to confirm that an exception will be raised if an
        IncarcerationAdmissionEvent is instantiated directly."""
        with self.assertRaises(Exception):
            _ = IncarcerationAdmissionEvent(
                state_code="US_XX",
                event_date=date(2000, 12, 1),
                facility="CJ10",
                county_of_residence=_COUNTY_OF_RESIDENCE,
            )


class TestCommitmentFromSupervisionEventForPeriod(unittest.TestCase):
    """Tests the _commitment_from_supervision_event_for_period function."""

    def setUp(self) -> None:
        self.identifier = identifier.IncarcerationIdentifier()

    def _run_commitment_from_supervision_event_for_period(
        self,
        incarceration_period: StateIncarcerationPeriod,
        pre_commitment_supervision_period: Optional[StateSupervisionPeriod],
        violation_delegate: StateSpecificViolationDelegate,
        supervision_delegate: StateSpecificSupervisionDelegate,
        incarceration_period_index: Optional[NormalizedIncarcerationPeriodIndex] = None,
        supervision_sentences: Optional[List[StateSupervisionSentence]] = None,
        incarceration_sentences: Optional[List[StateIncarcerationSentence]] = None,
        assessments: Optional[List[StateAssessment]] = None,
        violation_responses: Optional[List[StateSupervisionViolationResponse]] = None,
        commitment_from_supervision_delegate: Optional[
            StateSpecificCommitmentFromSupervisionDelegate
        ] = None,
        incarceration_delegate: Optional[StateSpecificIncarcerationDelegate] = None,
        supervision_period_to_agent_associations: Optional[
            Dict[int, Dict[str, Any]]
        ] = None,
    ) -> IncarcerationCommitmentFromSupervisionAdmissionEvent:
        """Helper function for testing the
        _commitment_from_supervision_event_for_period function."""
        supervision_sentences = supervision_sentences or []
        incarceration_sentences = incarceration_sentences or []
        assessments = assessments or []
        sorted_violation_responses = (
            sorted(violation_responses, key=lambda b: b.response_date or date.min)
            if violation_responses
            else []
        )
        commitment_from_supervision_delegate = (
            commitment_from_supervision_delegate
            or UsXxCommitmentFromSupervisionDelegate()
        )
        incarceration_delegate = incarceration_delegate or UsXxIncarcerationDelegate()

        incarceration_period_index = (
            incarceration_period_index
            or default_normalized_ip_index_for_tests(
                incarceration_periods=[incarceration_period],
                transfers_are_collapsed=True,
            )
        )
        supervision_period_index = default_normalized_sp_index_for_tests(
            supervision_periods=[pre_commitment_supervision_period]
            if pre_commitment_supervision_period
            else []
        )

        # pylint: disable=protected-access
        return self.identifier._commitment_from_supervision_event_for_period(
            incarceration_sentences=incarceration_sentences,
            supervision_sentences=supervision_sentences,
            incarceration_period=incarceration_period,
            incarceration_period_index=incarceration_period_index,
            supervision_period_index=supervision_period_index,
            assessments=assessments,
            sorted_violation_responses=sorted_violation_responses,
            supervision_period_to_agent_associations=supervision_period_to_agent_associations
            or _DEFAULT_SUPERVISION_PERIOD_AGENT_ASSOCIATIONS,
            county_of_residence=_COUNTY_OF_RESIDENCE,
            commitment_from_supervision_delegate=commitment_from_supervision_delegate,
            violation_delegate=violation_delegate,
            supervision_delegate=supervision_delegate,
            incarceration_delegate=incarceration_delegate,
        )

    def test_commitment_from_supervision_event_violation_history_cutoff(self) -> None:
        """Tests the _commitment_from_supervision_event_for_period function,
        specifically the logic that includes the violation reports within the violation
        window. The `old` response and violation fall within a year of the last
        violation response before the revocation admission, but not within a year of the
        revocation date. Test that the `old` response is included in the response
        history."""

        supervision_violation_1 = StateSupervisionViolation.new_with_defaults(
            supervision_violation_id=123455,
            state_code="US_XX",
            violation_date=date(2008, 12, 7),
            supervision_violation_types=[
                StateSupervisionViolationTypeEntry.new_with_defaults(
                    state_code="US_XX",
                    violation_type=StateSupervisionViolationType.FELONY,
                )
            ],
        )

        supervision_violation_response_1 = (
            StateSupervisionViolationResponse.new_with_defaults(
                state_code="US_XX",
                supervision_violation_response_id=_DEFAULT_SSVR_ID,
                response_type=StateSupervisionViolationResponseType.VIOLATION_REPORT,
                response_date=date(2008, 12, 7),
                supervision_violation_response_decisions=[
                    StateSupervisionViolationResponseDecisionEntry.new_with_defaults(
                        state_code="US_XX",
                        decision=StateSupervisionViolationResponseDecision.CONTINUANCE,
                    )
                ],
                supervision_violation=supervision_violation_1,
            )
        )

        supervision_violation_2 = StateSupervisionViolation.new_with_defaults(
            supervision_violation_id=123455,
            state_code="US_XX",
            violation_date=date(2009, 11, 13),
        )

        supervision_violation_response_2 = StateSupervisionViolationResponse.new_with_defaults(
            supervision_violation_response_id=_DEFAULT_SSVR_ID,
            response_type=StateSupervisionViolationResponseType.VIOLATION_REPORT,
            state_code="US_XX",
            response_date=date(2009, 11, 13),
            supervision_violation_response_decisions=[
                # This REVOCATION decision is the most severe, but this is not the most recent response
                StateSupervisionViolationResponseDecisionEntry.new_with_defaults(
                    state_code="US_XX",
                    decision=StateSupervisionViolationResponseDecision.REVOCATION,
                )
            ],
            supervision_violation=supervision_violation_2,
        )

        supervision_violation_3 = StateSupervisionViolation.new_with_defaults(
            state_code="US_XX",
            supervision_violation_id=6789,
            violation_date=date(2009, 12, 1),
            supervision_violation_types=[
                StateSupervisionViolationTypeEntry.new_with_defaults(
                    state_code="US_XX",
                    violation_type=StateSupervisionViolationType.TECHNICAL,
                )
            ],
        )

        supervision_violation_response_3 = (
            StateSupervisionViolationResponse.new_with_defaults(
                state_code="US_XX",
                supervision_violation_response_id=_DEFAULT_SSVR_ID,
                response_type=StateSupervisionViolationResponseType.VIOLATION_REPORT,
                response_date=date(2009, 12, 1),
                supervision_violation_response_decisions=[
                    StateSupervisionViolationResponseDecisionEntry.new_with_defaults(
                        state_code="US_XX",
                        decision=StateSupervisionViolationResponseDecision.CONTINUANCE,
                    )
                ],
                supervision_violation=supervision_violation_3,
            )
        )

        supervision_period = StateSupervisionPeriod.new_with_defaults(
            supervision_period_id=_DEFAULT_SP_ID,
            external_id="sp1",
            state_code="US_XX",
            start_date=date(2008, 3, 5),
            termination_date=date(2009, 12, 19),
            supervision_type=StateSupervisionPeriodSupervisionType.PROBATION,
            supervision_site="OFFICE_1",
        )

        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=111,
            external_id="ip1",
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            admission_date=date(2009, 12, 31),
            admission_reason=StateIncarcerationPeriodAdmissionReason.REVOCATION,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )

        violation_responses = [
            supervision_violation_response_1,
            supervision_violation_response_2,
            supervision_violation_response_3,
        ]

        commitment_from_supervision_event = (
            self._run_commitment_from_supervision_event_for_period(
                pre_commitment_supervision_period=supervision_period,
                incarceration_period=incarceration_period,
                violation_responses=violation_responses,
                violation_delegate=UsXxViolationDelegate(),
                supervision_delegate=UsXxSupervisionDelegate(),
            )
        )

        supervision_type = StateSupervisionPeriodSupervisionType.PROBATION

        assert incarceration_period.admission_date is not None
        assert incarceration_period.admission_reason is not None
        expected_commitment_from_supervision_event = IncarcerationCommitmentFromSupervisionAdmissionEvent(
            state_code=supervision_period.state_code,
            event_date=incarceration_period.admission_date,
            admission_reason=incarceration_period.admission_reason,
            supervision_type=supervision_type,
            case_type=StateSupervisionCaseType.GENERAL,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            most_severe_violation_type=StateSupervisionViolationType.FELONY,
            most_severe_violation_type_subtype=StateSupervisionViolationType.FELONY.value,
            most_severe_response_decision=StateSupervisionViolationResponseDecision.REVOCATION,
            most_recent_response_decision=StateSupervisionViolationResponseDecision.CONTINUANCE,
            response_count=3,
            violation_history_description="1felony;1technical",
            violation_type_frequency_counter=[["FELONY"], ["TECHNICAL"]],
            supervising_officer_external_id="XXX",
            supervising_district_external_id="OFFICE_1",
            level_1_supervision_location_external_id="OFFICE_1",
            county_of_residence=_COUNTY_OF_RESIDENCE,
            assessment_score_bucket=DEFAULT_ASSESSMENT_SCORE_BUCKET,
        )

        self.assertEqual(
            expected_commitment_from_supervision_event,
            commitment_from_supervision_event,
        )

    def test_commitment_from_supervision_event_before_violation_history_cutoff(
        self,
    ) -> None:
        """Tests the _commitment_from_supervision_event_for_period function, specifically the logic that includes the violation
        reports within the violation window. The `old` response and violation falls before the violation history
        window. Test that the `old` response is not included in the response history."""

        supervision_violation_old = StateSupervisionViolation.new_with_defaults(
            supervision_violation_id=123455,
            state_code="US_XX",
            violation_date=date(2007, 12, 7),
            supervision_violation_types=[
                StateSupervisionViolationTypeEntry.new_with_defaults(
                    state_code="US_XX",
                    violation_type=StateSupervisionViolationType.FELONY,
                )
            ],
        )

        supervision_violation_response_old = (
            StateSupervisionViolationResponse.new_with_defaults(
                state_code="US_XX",
                supervision_violation_response_id=_DEFAULT_SSVR_ID,
                response_type=StateSupervisionViolationResponseType.VIOLATION_REPORT,
                response_date=date(2007, 12, 7),
                supervision_violation_response_decisions=[
                    StateSupervisionViolationResponseDecisionEntry.new_with_defaults(
                        state_code="US_XX",
                        decision=StateSupervisionViolationResponseDecision.REVOCATION,
                    )
                ],
                supervision_violation=supervision_violation_old,
            )
        )

        supervision_violation = StateSupervisionViolation.new_with_defaults(
            state_code="US_XX",
            supervision_violation_id=6789,
            violation_date=date(2009, 12, 1),
            supervision_violation_types=[
                StateSupervisionViolationTypeEntry.new_with_defaults(
                    state_code="US_XX",
                    violation_type=StateSupervisionViolationType.TECHNICAL,
                )
            ],
        )

        supervision_violation_response = (
            StateSupervisionViolationResponse.new_with_defaults(
                state_code="US_XX",
                supervision_violation_response_id=_DEFAULT_SSVR_ID,
                response_type=StateSupervisionViolationResponseType.VIOLATION_REPORT,
                response_date=date(2009, 12, 1),
                supervision_violation_response_decisions=[
                    StateSupervisionViolationResponseDecisionEntry.new_with_defaults(
                        state_code="US_XX",
                        decision=StateSupervisionViolationResponseDecision.REVOCATION,
                    ),
                    StateSupervisionViolationResponseDecisionEntry.new_with_defaults(
                        state_code="US_XX",
                        decision=StateSupervisionViolationResponseDecision.CONTINUANCE,
                    ),
                ],
                supervision_violation=supervision_violation,
            )
        )

        supervision_period = StateSupervisionPeriod.new_with_defaults(
            supervision_period_id=_DEFAULT_SP_ID,
            external_id="sp1",
            state_code="US_XX",
            start_date=date(2008, 3, 5),
            termination_date=date(2009, 12, 19),
            supervision_type=StateSupervisionPeriodSupervisionType.PROBATION,
            supervision_site="OFFICE_1",
        )

        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=111,
            external_id="ip1",
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            admission_date=date(2009, 12, 31),
            admission_reason=StateIncarcerationPeriodAdmissionReason.REVOCATION,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )

        violation_responses = [
            supervision_violation_response,
            supervision_violation_response_old,
        ]

        commitment_from_supervision_event = (
            self._run_commitment_from_supervision_event_for_period(
                pre_commitment_supervision_period=supervision_period,
                incarceration_period=incarceration_period,
                violation_responses=violation_responses,
                violation_delegate=UsXxViolationDelegate(),
                supervision_delegate=UsXxSupervisionDelegate(),
            )
        )

        supervision_type = StateSupervisionPeriodSupervisionType.PROBATION

        assert incarceration_period.admission_date is not None
        assert incarceration_period.admission_reason is not None
        expected_commitment_from_supervision_event = IncarcerationCommitmentFromSupervisionAdmissionEvent(
            state_code=supervision_period.state_code,
            event_date=incarceration_period.admission_date,
            admission_reason=incarceration_period.admission_reason,
            supervision_type=supervision_type,
            case_type=StateSupervisionCaseType.GENERAL,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            most_severe_violation_type=StateSupervisionViolationType.TECHNICAL,
            most_severe_violation_type_subtype=StateSupervisionViolationType.TECHNICAL.value,
            most_severe_response_decision=StateSupervisionViolationResponseDecision.REVOCATION,
            most_recent_response_decision=StateSupervisionViolationResponseDecision.REVOCATION,
            response_count=1,
            violation_history_description="1technical",
            violation_type_frequency_counter=[["TECHNICAL"]],
            supervising_officer_external_id="XXX",
            supervising_district_external_id="OFFICE_1",
            level_1_supervision_location_external_id="OFFICE_1",
            county_of_residence=_COUNTY_OF_RESIDENCE,
            assessment_score_bucket=DEFAULT_ASSESSMENT_SCORE_BUCKET,
        )

        self.assertEqual(
            expected_commitment_from_supervision_event,
            commitment_from_supervision_event,
        )

    def test_commitment_from_supervision_event_us_mo_ignore_supplemental_for_lookback_date(
        self,
    ) -> None:
        """Tests the _commitment_from_supervision_event_for_period function, specifically the logic that includes the violation
        reports within the violation window. The most recent response prior to the revocation is a supplemental report,
        which should not be included when determining the date of the most recent response for the violation history
        window. Tests that the date on the most recent non-supplemental report is used for the violation history, but
        that the response decision on the supplemental report is counted for the most_severe_response_decision.
        """
        state_code = "US_MO"

        supervision_violation = StateSupervisionViolation.new_with_defaults(
            supervision_violation_id=123455,
            state_code=state_code,
            violation_date=date(2008, 12, 7),
            supervision_violation_types=[
                StateSupervisionViolationTypeEntry.new_with_defaults(
                    state_code=state_code,
                    violation_type=StateSupervisionViolationType.FELONY,
                )
            ],
        )

        supervision_violation_response = (
            StateSupervisionViolationResponse.new_with_defaults(
                state_code=state_code,
                supervision_violation_response_id=_DEFAULT_SSVR_ID,
                response_type=StateSupervisionViolationResponseType.VIOLATION_REPORT,
                response_subtype="INI",
                response_date=date(2008, 12, 7),
                supervision_violation_response_decisions=[
                    StateSupervisionViolationResponseDecisionEntry.new_with_defaults(
                        state_code=state_code,
                        decision=StateSupervisionViolationResponseDecision.REVOCATION,
                    )
                ],
                supervision_violation=supervision_violation,
            )
        )

        supervision_violation_sup = StateSupervisionViolation.new_with_defaults(
            state_code=state_code,
            supervision_violation_id=6789,
            violation_date=date(2012, 12, 1),
            supervision_violation_types=[
                StateSupervisionViolationTypeEntry.new_with_defaults(
                    state_code=state_code,
                    violation_type=StateSupervisionViolationType.TECHNICAL,
                )
            ],
        )

        supervision_violation_response_sup = StateSupervisionViolationResponse.new_with_defaults(
            state_code=state_code,
            supervision_violation_response_id=_DEFAULT_SSVR_ID,
            response_type=StateSupervisionViolationResponseType.VIOLATION_REPORT,
            response_subtype="SUP",
            response_date=date(2012, 12, 1),
            supervision_violation_response_decisions=[
                StateSupervisionViolationResponseDecisionEntry.new_with_defaults(
                    state_code=state_code,
                    decision=StateSupervisionViolationResponseDecision.SHOCK_INCARCERATION,
                )
            ],
            supervision_violation=supervision_violation_sup,
        )

        supervision_period = StateSupervisionPeriod.new_with_defaults(
            supervision_period_id=_DEFAULT_SP_ID,
            external_id="sp1",
            state_code=state_code,
            start_date=date(2008, 3, 5),
            termination_date=date(2012, 12, 19),
            supervision_type=StateSupervisionPeriodSupervisionType.PROBATION,
            supervision_site="OFFICE_1",
        )

        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=111,
            external_id="ip1",
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code=state_code,
            admission_date=date(2012, 12, 31),
            admission_reason=StateIncarcerationPeriodAdmissionReason.REVOCATION,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )

        assert supervision_period.start_date is not None
        assert supervision_period.termination_date is not None
        supervision_sentence = FakeUsMoSupervisionSentence.fake_sentence_from_sentence(
            StateSupervisionSentence.new_with_defaults(
                state_code="US_MO",
                supervision_sentence_id=111,
                start_date=date(2008, 3, 5),
                external_id="ss1",
                supervision_type=StateSupervisionSentenceSupervisionType.PROBATION,
                status=StateSentenceStatus.REVOKED,
                completion_date=date(2018, 5, 19),
            ),
            supervision_type_spans=[
                SupervisionTypeSpan(
                    start_date=supervision_period.start_date,
                    end_date=supervision_period.termination_date,
                    supervision_type=StateSupervisionSentenceSupervisionType.PROBATION,
                    start_critical_statuses=[
                        UsMoSentenceStatus(
                            sentence_external_id="123",
                            sentence_status_external_id="test-status-1",
                            status_date=date(2010, 1, 1),
                            status_code="40I2000",
                            status_description="Prob Rev-Technical",
                            person_external_id="1",
                            is_supervision_type_critical_status=False,
                            is_supervision_out_status=False,
                            is_supervision_in_status=False,
                            is_incarceration_in_status=False,
                            is_incarceration_out_status=False,
                            is_lifetime_supervision_start_status=False,
                            is_sentence_termination_status_candidate=False,
                            is_investigation_status=False,
                            is_sentence_termimination_status=False,
                        )
                    ],
                    end_critical_statuses=[],
                ),
                SupervisionTypeSpan(
                    start_date=supervision_period.termination_date,
                    end_date=None,
                    supervision_type=None,
                    start_critical_statuses=[],
                    end_critical_statuses=None,
                ),
            ],
        )

        assert incarceration_period.admission_date is not None
        incarceration_sentence = (
            FakeUsMoIncarcerationSentence.fake_sentence_from_sentence(
                StateIncarcerationSentence.new_with_defaults(
                    state_code="US_MO",
                    incarceration_sentence_id=123,
                    external_id="is1",
                    start_date=date(2018, 5, 25),
                    status=StateSentenceStatus.PRESENT_WITHOUT_INFO,
                ),
                supervision_type_spans=[
                    SupervisionTypeSpan(
                        start_date=incarceration_period.admission_date,
                        end_date=None,
                        supervision_type=None,
                        start_critical_statuses=[],
                        end_critical_statuses=None,
                    )
                ],
            )
        )

        violation_responses = [
            supervision_violation_response,
            supervision_violation_response_sup,
        ]

        commitment_from_supervision_event = (
            self._run_commitment_from_supervision_event_for_period(
                pre_commitment_supervision_period=supervision_period,
                incarceration_period=incarceration_period,
                violation_responses=violation_responses,
                supervision_sentences=[supervision_sentence],
                incarceration_sentences=[incarceration_sentence],
                violation_delegate=UsMoViolationDelegate(),
                supervision_delegate=UsMoSupervisionDelegate(),
                supervision_period_to_agent_associations={
                    _DEFAULT_SP_ID: {
                        "agent_id": 000,
                        "agent_external_id": "XXX",
                        "supervision_period_id": _DEFAULT_SP_ID,
                        "agent_start_date": date(2008, 3, 5),
                        "agent_end_date": date(2012, 12, 19),
                    }
                },
            )
        )

        supervision_type = StateSupervisionPeriodSupervisionType.PROBATION

        assert incarceration_period.admission_date is not None
        assert incarceration_period.admission_reason is not None
        expected_commitment_from_supervision_event = IncarcerationCommitmentFromSupervisionAdmissionEvent(
            state_code=supervision_period.state_code,
            event_date=incarceration_period.admission_date,
            admission_reason=incarceration_period.admission_reason,
            supervision_type=supervision_type,
            case_type=StateSupervisionCaseType.GENERAL,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            most_severe_violation_type=StateSupervisionViolationType.FELONY,
            most_severe_violation_type_subtype=StateSupervisionViolationType.FELONY.value,
            most_severe_response_decision=StateSupervisionViolationResponseDecision.REVOCATION,
            most_recent_response_decision=StateSupervisionViolationResponseDecision.SHOCK_INCARCERATION,
            response_count=1,
            violation_history_description="1fel",
            violation_type_frequency_counter=[["FELONY"]],
            supervising_officer_external_id="XXX",
            supervising_district_external_id="OFFICE_1",
            level_1_supervision_location_external_id="OFFICE_1",
            county_of_residence=_COUNTY_OF_RESIDENCE,
            assessment_score_bucket=DEFAULT_ASSESSMENT_SCORE_BUCKET,
        )

        self.assertEqual(
            expected_commitment_from_supervision_event,
            commitment_from_supervision_event,
        )

    def test_commitment_from_supervision_event_us_nd(self) -> None:
        supervision_period = StateSupervisionPeriod.new_with_defaults(
            supervision_period_id=_DEFAULT_SP_ID,
            external_id="sp1",
            state_code="US_ND",
            start_date=date(2018, 3, 5),
            termination_date=date(2018, 5, 19),
            supervision_type=StateSupervisionPeriodSupervisionType.PAROLE,
            supervision_site="X",
        )

        supervision_violation = StateSupervisionViolation.new_with_defaults(
            supervision_violation_id=123455,
            state_code="US_ND",
            violation_date=date(2018, 4, 20),
            supervision_violation_types=[
                StateSupervisionViolationTypeEntry.new_with_defaults(
                    state_code="US_ND",
                    violation_type=StateSupervisionViolationType.FELONY,
                ),
            ],
        )

        ssvr = StateSupervisionViolationResponse.new_with_defaults(
            state_code="US_ND",
            supervision_violation_response_id=_DEFAULT_SSVR_ID,
            supervision_violation=supervision_violation,
            response_date=date(2018, 5, 25),
            response_type=StateSupervisionViolationResponseType.PERMANENT_DECISION,
        )

        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=111,
            external_id="ip1",
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_ND",
            admission_date=date(2018, 6, 3),
            admission_reason=StateIncarcerationPeriodAdmissionReason.REVOCATION,
            admission_reason_raw_text="PARL",
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )

        supervision_sentence = StateSupervisionSentence.new_with_defaults(
            state_code="US_ND",
            supervision_sentence_id=111,
            start_date=date(2017, 1, 1),
            external_id="ss1",
            status=StateSentenceStatus.COMPLETED,
            supervision_type=StateSupervisionSentenceSupervisionType.PROBATION,
        )

        commitment_from_supervision_event = self._run_commitment_from_supervision_event_for_period(
            pre_commitment_supervision_period=supervision_period,
            incarceration_period=incarceration_period,
            violation_responses=[ssvr],
            supervision_sentences=[supervision_sentence],
            incarceration_sentences=[],
            commitment_from_supervision_delegate=UsNdCommitmentFromSupervisionDelegate(),
            violation_delegate=UsNdViolationDelegate(),
            supervision_delegate=UsNdSupervisionDelegate(),
        )

        assert incarceration_period.admission_date is not None
        assert incarceration_period.admission_reason is not None
        expected_commitment_from_supervision_event = IncarcerationCommitmentFromSupervisionAdmissionEvent(
            state_code=supervision_period.state_code,
            event_date=incarceration_period.admission_date,
            admission_reason=incarceration_period.admission_reason,
            admission_reason_raw_text=incarceration_period.admission_reason_raw_text,
            supervision_type=StateSupervisionPeriodSupervisionType.PAROLE,
            case_type=StateSupervisionCaseType.GENERAL,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            most_severe_violation_type=StateSupervisionViolationType.FELONY,
            most_severe_violation_type_subtype=StateSupervisionViolationType.FELONY.value,
            response_count=1,
            violation_history_description="1felony",
            violation_type_frequency_counter=[["FELONY"]],
            supervising_officer_external_id="XXX",
            supervising_district_external_id="X",
            level_1_supervision_location_external_id="X",
            county_of_residence=_COUNTY_OF_RESIDENCE,
            assessment_score_bucket=DEFAULT_ASSESSMENT_SCORE_BUCKET,
        )

        self.assertEqual(
            expected_commitment_from_supervision_event,
            commitment_from_supervision_event,
        )


class TestReleaseEventForPeriod(unittest.TestCase):
    """Tests the release_event_for_period function."""

    def setUp(self) -> None:
        self.identifier = identifier.IncarcerationIdentifier()

    def _run_release_for_period_with_no_sentences(
        self,
        incarceration_period: StateIncarcerationPeriod,
        county_of_residence: Optional[str],
        incarceration_delegate: Optional[StateSpecificIncarcerationDelegate] = None,
        supervision_delegate: Optional[StateSpecificSupervisionDelegate] = None,
    ) -> Optional[IncarcerationReleaseEvent]:
        """Runs `release_event_for_period` without providing sentence information. Sentence information
        is only used to inform supervision_type_at_release for US_MO and US_ID. All tests using this method should
        not require that state specific logic.
        """

        incarceration_delegate = incarceration_delegate or UsXxIncarcerationDelegate()
        incarceration_period_index = default_normalized_ip_index_for_tests(
            incarceration_periods=[incarceration_period],
            transfers_are_collapsed=True,
        )

        supervision_period_index = default_normalized_sp_index_for_tests()

        incarceration_delegate = incarceration_delegate or UsXxIncarcerationDelegate()
        supervision_delegate = supervision_delegate or UsXxSupervisionDelegate()

        # pylint: disable=protected-access
        return self.identifier._release_event_for_period(
            incarceration_period,
            incarceration_period_index,
            supervision_period_index,
            incarceration_delegate,
            supervision_delegate,
            {},  # commitments from supervision
            county_of_residence,
        )

    def test_release_event_for_period(self) -> None:
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            facility="PRISON3",
            admission_date=date(2008, 11, 20),
            admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.TREATMENT_IN_PRISON,
            release_date=date(2010, 12, 4),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
            release_reason_raw_text="SS",
        )

        release_event = self._run_release_for_period_with_no_sentences(
            incarceration_period, _COUNTY_OF_RESIDENCE
        )

        assert incarceration_period.release_reason is not None
        assert incarceration_period.release_date is not None
        assert incarceration_period.admission_date is not None
        self.assertEqual(
            IncarcerationReleaseEvent(
                state_code=incarceration_period.state_code,
                event_date=incarceration_period.release_date,
                facility="PRISON3",
                county_of_residence=_COUNTY_OF_RESIDENCE,
                release_reason=incarceration_period.release_reason,
                release_reason_raw_text=incarceration_period.release_reason_raw_text,
                purpose_for_incarceration=incarceration_period.specialized_purpose_for_incarceration,
                admission_reason=incarceration_period.admission_reason,
                total_days_incarcerated=(
                    incarceration_period.release_date
                    - incarceration_period.admission_date
                ).days,
            ),
            release_event,
        )

    def test_release_event_for_period_all_release_reasons(self) -> None:
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_XX",
            facility="PRISON3",
            admission_date=date(2013, 11, 20),
            admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            release_date=date(2019, 12, 4),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
        )

        for release_reason in StateIncarcerationPeriodReleaseReason:
            incarceration_period.release_reason = release_reason

            release_event = self._run_release_for_period_with_no_sentences(
                incarceration_period, _COUNTY_OF_RESIDENCE
            )

            self.assertIsNotNone(release_event)

    def test_release_event_for_period_county_jail(self) -> None:
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            incarceration_type=StateIncarcerationType.COUNTY_JAIL,
            state_code="US_XX",
            facility="CJ19",
            admission_date=date(2013, 11, 20),
            admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            release_date=date(2019, 12, 4),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
        )

        release_event = self._run_release_for_period_with_no_sentences(
            incarceration_period, _COUNTY_OF_RESIDENCE
        )

        assert incarceration_period.release_reason is not None
        assert incarceration_period.release_date is not None
        assert incarceration_period.admission_date is not None
        self.assertEqual(
            IncarcerationReleaseEvent(
                state_code=incarceration_period.state_code,
                event_date=incarceration_period.release_date,
                facility="CJ19",
                county_of_residence=_COUNTY_OF_RESIDENCE,
                release_reason=incarceration_period.release_reason,
                admission_reason=incarceration_period.admission_reason,
                total_days_incarcerated=(
                    incarceration_period.release_date
                    - incarceration_period.admission_date
                ).days,
                purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            ),
            release_event,
        )

    def test_release_event_for_period_us_id(self) -> None:
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_ID",
            facility="PRISON3",
            admission_date=date(2008, 11, 20),
            admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.TREATMENT_IN_PRISON,
            release_date=date(2010, 12, 4),
            release_reason=StateIncarcerationPeriodReleaseReason.CONDITIONAL_RELEASE,
            release_reason_raw_text="SS",
        )

        supervision_period = StateSupervisionPeriod.new_with_defaults(
            state_code="US_ID",
            supervision_period_id=111,
            start_date=incarceration_period.release_date,
            supervision_type=StateSupervisionPeriodSupervisionType.PROBATION,
        )
        incarceration_delegate = UsIdIncarcerationDelegate()
        supervision_delegate = UsIdSupervisionDelegate()

        incarceration_period_index = default_normalized_ip_index_for_tests(
            incarceration_periods=[incarceration_period],
            transfers_are_collapsed=True,
        )

        supervision_period_index = default_normalized_sp_index_for_tests(
            supervision_periods=[supervision_period]
        )

        # pylint: disable=protected-access
        release_event = self.identifier._release_event_for_period(
            incarceration_period=incarceration_period,
            incarceration_period_index=incarceration_period_index,
            supervision_period_index=supervision_period_index,
            incarceration_delegate=incarceration_delegate,
            supervision_delegate=supervision_delegate,
            commitments_from_supervision={},
            county_of_residence=_COUNTY_OF_RESIDENCE,
        )

        assert incarceration_period.release_reason is not None
        assert incarceration_period.release_date is not None
        assert incarceration_period.admission_date is not None
        self.assertEqual(
            IncarcerationReleaseEvent(
                state_code=incarceration_period.state_code,
                event_date=incarceration_period.release_date,
                facility="PRISON3",
                county_of_residence=_COUNTY_OF_RESIDENCE,
                release_reason=incarceration_period.release_reason,
                release_reason_raw_text=incarceration_period.release_reason_raw_text,
                purpose_for_incarceration=incarceration_period.specialized_purpose_for_incarceration,
                supervision_type_at_release=StateSupervisionPeriodSupervisionType.PROBATION,
                admission_reason=incarceration_period.admission_reason,
                total_days_incarcerated=(
                    incarceration_period.release_date
                    - incarceration_period.admission_date
                ).days,
            ),
            release_event,
        )

    def test_release_event_for_period_us_mo(self) -> None:
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_MO",
            facility="PRISON3",
            admission_date=date(2013, 11, 20),
            admission_reason=StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            release_date=date(2019, 12, 4),
            release_reason=StateIncarcerationPeriodReleaseReason.CONDITIONAL_RELEASE,
        )
        supervision_period = StateSupervisionPeriod.new_with_defaults(
            supervision_period_id=1111,
            state_code="US_MO",
            start_date=date(2019, 12, 4),
            supervision_type=StateSupervisionPeriodSupervisionType.PROBATION,
        )
        incarceration_delegate = UsMoIncarcerationDelegate()
        supervision_delegate = UsMoSupervisionDelegate()

        incarceration_period_index = default_normalized_ip_index_for_tests(
            incarceration_periods=[incarceration_period],
            transfers_are_collapsed=True,
        )

        supervision_period_index = default_normalized_sp_index_for_tests(
            supervision_periods=[supervision_period]
        )

        # pylint: disable=protected-access
        release_event = self.identifier._release_event_for_period(
            incarceration_period=incarceration_period,
            incarceration_period_index=incarceration_period_index,
            supervision_period_index=supervision_period_index,
            incarceration_delegate=incarceration_delegate,
            supervision_delegate=supervision_delegate,
            commitments_from_supervision={},
            county_of_residence=_COUNTY_OF_RESIDENCE,
        )

        assert incarceration_period.release_date is not None
        assert incarceration_period.release_reason is not None
        assert incarceration_period.admission_date is not None
        self.assertEqual(
            IncarcerationReleaseEvent(
                state_code=incarceration_period.state_code,
                event_date=incarceration_period.release_date,
                facility="PRISON3",
                county_of_residence=_COUNTY_OF_RESIDENCE,
                release_reason=incarceration_period.release_reason,
                release_reason_raw_text=incarceration_period.release_reason_raw_text,
                purpose_for_incarceration=incarceration_period.specialized_purpose_for_incarceration,
                supervision_type_at_release=StateSupervisionPeriodSupervisionType.PROBATION,
                admission_reason=incarceration_period.admission_reason,
                total_days_incarcerated=(
                    incarceration_period.release_date
                    - incarceration_period.admission_date
                ).days,
            ),
            release_event,
        )

    def test_release_event_for_period_us_nd(self) -> None:
        admission_date = date(2008, 11, 20)
        release_date = date(2010, 12, 4)
        admission_reason = StateIncarcerationPeriodAdmissionReason.NEW_ADMISSION
        release_reason = StateIncarcerationPeriodReleaseReason.CONDITIONAL_RELEASE
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=1111,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            state_code="US_ND",
            facility="NDSP",
            custodial_authority=StateCustodialAuthority.STATE_PRISON,
            admission_date=admission_date,
            admission_reason=admission_reason,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.TREATMENT_IN_PRISON,
            release_date=release_date,
            release_reason=release_reason,
            release_reason_raw_text="RPAR",
        )
        supervision_period = StateSupervisionPeriod.new_with_defaults(
            supervision_period_id=1112,
            state_code="US_ND",
            supervision_type=StateSupervisionPeriodSupervisionType.PAROLE,
            start_date=date(2010, 12, 4),
        )

        incarceration_period_index = default_normalized_ip_index_for_tests(
            incarceration_periods=[incarceration_period],
            transfers_are_collapsed=True,
        )

        supervision_period_index = default_normalized_sp_index_for_tests(
            supervision_periods=[supervision_period]
        )

        # pylint: disable=protected-access
        release_event = self.identifier._release_event_for_period(
            incarceration_period,
            incarceration_period_index,
            supervision_period_index,
            UsNdIncarcerationDelegate(),
            UsNdSupervisionDelegate(),
            {},
            _COUNTY_OF_RESIDENCE,
        )

        self.assertEqual(
            IncarcerationReleaseEvent(
                state_code=incarceration_period.state_code,
                event_date=release_date,
                facility=incarceration_period.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                release_reason=release_reason,
                release_reason_raw_text=incarceration_period.release_reason_raw_text,
                purpose_for_incarceration=incarceration_period.specialized_purpose_for_incarceration,
                supervision_type_at_release=StateSupervisionPeriodSupervisionType.PAROLE,
                admission_reason=admission_reason,
                total_days_incarcerated=(release_date - admission_date).days,
            ),
            release_event,
        )


def expected_incarceration_stay_events(
    incarceration_period: StateIncarcerationPeriod,
    original_admission_reason: Optional[StateIncarcerationPeriodAdmissionReason] = None,
    original_admission_reason_raw_text: Optional[str] = None,
    judicial_district_code: Optional[str] = None,
    commitment_from_supervision_supervision_type: Optional[
        StateSupervisionPeriodSupervisionType
    ] = None,
    included_in_state_population: bool = True,
) -> List[IncarcerationStayEvent]:
    """Returns the expected incarceration stay events based on the provided |incarceration_period|."""

    expected_incarceration_events = []

    original_admission_reason = (
        original_admission_reason
        if original_admission_reason
        else incarceration_period.admission_reason
    )

    original_admission_reason_raw_text = (
        original_admission_reason_raw_text
        if original_admission_reason_raw_text
        else incarceration_period.admission_reason_raw_text
    )

    purpose_for_incarceration = (
        incarceration_period.specialized_purpose_for_incarceration
        or StateSpecializedPurposeForIncarceration.GENERAL
    )

    if incarceration_period.admission_date:
        release_date = min(
            (incarceration_period.release_date or date.max),
            date.today() + relativedelta(days=1),
        )

        days_incarcerated = [
            incarceration_period.admission_date + relativedelta(days=x)
            for x in range((release_date - incarceration_period.admission_date).days)
        ]

        if days_incarcerated:
            # Ensuring we're not counting the release date as a day spent incarcerated
            assert max(days_incarcerated) < release_date

        for stay_date in days_incarcerated:
            event = IncarcerationStayEvent(
                admission_reason=original_admission_reason,
                admission_reason_raw_text=original_admission_reason_raw_text,
                state_code=incarceration_period.state_code,
                facility=incarceration_period.facility,
                county_of_residence=_COUNTY_OF_RESIDENCE,
                event_date=stay_date,
                judicial_district_code=judicial_district_code,
                specialized_purpose_for_incarceration=purpose_for_incarceration,
                commitment_from_supervision_supervision_type=commitment_from_supervision_supervision_type,
                included_in_state_population=included_in_state_population,
            )

            expected_incarceration_events.append(event)

    return expected_incarceration_events