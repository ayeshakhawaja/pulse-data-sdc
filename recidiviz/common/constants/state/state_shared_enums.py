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

"""Constants shared across a few different entities."""
from enum import unique
from typing import Dict

from recidiviz.common.constants.state import (
    enum_canonical_strings as state_enum_strings,
)
from recidiviz.common.constants.state.state_entity_enum import StateEntityEnum


# TODO(#8905): Delete _get_default_map() once all state ingest views have been
#  migrated to v2 mappings.
@unique
class StateActingBodyType(StateEntityEnum):
    """Any person or persons who is taking an action."""

    COURT = state_enum_strings.state_acting_body_type_court
    PAROLE_BOARD = state_enum_strings.state_acting_body_type_parole_board
    SUPERVISION_OFFICER = state_enum_strings.state_acting_body_type_supervision_officer
    SENTENCED_PERSON = state_enum_strings.state_acting_body_type_sentenced_person
    INTERNAL_UNKNOWN = state_enum_strings.internal_unknown
    EXTERNAL_UNKNOWN = state_enum_strings.external_unknown

    @staticmethod
    def _get_default_map() -> Dict[str, "StateActingBodyType"]:
        return _STATE_ACTING_BODY_TYPE_MAP


_STATE_ACTING_BODY_TYPE_MAP = {
    "COURT": StateActingBodyType.COURT,
    "PAROLE BOARD": StateActingBodyType.PAROLE_BOARD,
    "SUPERVISION OFFICER": StateActingBodyType.SUPERVISION_OFFICER,
    "SENTENCED PERSON": StateActingBodyType.SENTENCED_PERSON,
    "INTERNAL UNKNOWN": StateActingBodyType.INTERNAL_UNKNOWN,
    "EXTERNAL UNKNOWN": StateActingBodyType.EXTERNAL_UNKNOWN,
}


# TODO(#8905): Delete _get_default_map() once all state ingest views have been
#  migrated to v2 mappings.
@unique
class StateCustodialAuthority(StateEntityEnum):
    """The type of government entity directly responsible for the person on a period of incarceration or supervision.
    Generally the entity of the agent who is filling out the paperwork and making recommendations for the person. This
    is not necessarily the decision making authority on the period."""

    COURT = state_enum_strings.state_custodial_authority_court

    FEDERAL = state_enum_strings.state_custodial_authority_federal

    OTHER_COUNTRY = state_enum_strings.state_custodial_authority_other_country
    OTHER_STATE = state_enum_strings.state_custodial_authority_other_state
    SUPERVISION_AUTHORITY = (
        state_enum_strings.state_custodial_authority_supervision_authority
    )
    STATE_PRISON = state_enum_strings.state_custodial_authority_state_prison
    INTERNAL_UNKNOWN = state_enum_strings.internal_unknown
    EXTERNAL_UNKNOWN = state_enum_strings.external_unknown

    @staticmethod
    def _get_default_map() -> Dict[str, "StateCustodialAuthority"]:
        return _STATE_CUSTODIAL_AUTHORITY_MAP


_STATE_CUSTODIAL_AUTHORITY_MAP = {
    "COURT": StateCustodialAuthority.COURT,
    "EXTERNAL UNKNOWN": StateCustodialAuthority.EXTERNAL_UNKNOWN,
    "FEDERAL": StateCustodialAuthority.FEDERAL,
    "INTERNAL UNKNOWN": StateCustodialAuthority.INTERNAL_UNKNOWN,
    "OTHER COUNTRY": StateCustodialAuthority.OTHER_COUNTRY,
    "OTHER STATE": StateCustodialAuthority.OTHER_STATE,
    "SUPERVISION AUTHORITY": StateCustodialAuthority.SUPERVISION_AUTHORITY,
    "STATE PRISON": StateCustodialAuthority.STATE_PRISON,
}