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
"""Contains the logic for a ViolationResponseNormalizationManager that manages the
normalization of StateSupervisionViolationResponse entities in the calculation
pipelines. """
import datetime
from collections import defaultdict
from copy import deepcopy
from typing import Dict, List, Optional, Set

import attr

from recidiviz.common.constants.state.state_supervision_violation import (
    StateSupervisionViolationType,
)
from recidiviz.persistence.entity.state.entities import (
    StateSupervisionViolatedConditionEntry,
    StateSupervisionViolation,
    StateSupervisionViolationResponse,
    StateSupervisionViolationTypeEntry,
)


class StateSpecificViolationResponseNormalizationDelegate:
    """Interface for state-specific decisions involved in normalization violation
    responses for calculations."""

    # TODO(#8781):  We will eventually want to do some variation of this logic for
    #  all states, which would mean that we don't have a
    #  should_de_duplicate_responses_by_date() function on the delegate
    def should_de_duplicate_responses_by_date(self) -> bool:
        """Whether or not responses should be de-duplicated by response date for the
        state. The default behavior is not to perform any de-duplication of
        StateSupervisionViolationResponse entities by response date."""
        return False

    def get_additional_violation_types_for_response(
        self,
        response: StateSupervisionViolationResponse,  # pylint: disable=unused-argument
    ) -> List[StateSupervisionViolationTypeEntry]:
        """Returns the list of additional violation types that need to be added to a
        StateSupervisionViolationResponse's list of supervision_violation_types. By
        default, there are no additional types to be returned."""
        return []

    def update_condition(
        self,
        response: StateSupervisionViolationResponse,  # pylint: disable=unused-argument
        condition_entry: StateSupervisionViolatedConditionEntry,
    ) -> StateSupervisionViolatedConditionEntry:
        """Updates the |condition_entry| on the |response|, if necessary, and returns
        the updated |condition_entry|.

        By default, returns the original |condition_entry| without updates."""
        return condition_entry


class ViolationResponseNormalizationManager:
    """Interface for generalized and state-specific normalization of
    StateSupervisionViolationResponses for use in calculations."""

    def __init__(
        self,
        violation_responses: List[StateSupervisionViolationResponse],
        delegate: StateSpecificViolationResponseNormalizationDelegate,
    ):
        self._violation_responses = deepcopy(violation_responses)
        self.delegate = delegate

    def normalized_violation_responses_for_calculations(
        self,
    ) -> List[StateSupervisionViolationResponse]:
        """Performs normalization on violation responses. Filters out draft
        responses or those with null dates, sorts responses by `response_date`,
        updates missing violation data (if needed by the state), de-duplicates
        responses by date (if the state delegate says we should), and returns the
        list of sorted, normalized StateSupervisionViolationResponses."""

        # Make a deep copy of the original violation responses to preprocess
        responses_for_normalization = deepcopy(self._violation_responses)

        filtered_responses = self._drop_responses_from_calculations(
            responses_for_normalization
        )
        sorted_responses = self._sorted_violation_responses(filtered_responses)
        updated_responses = self._update_violations_on_responses(sorted_responses)
        if self.delegate.should_de_duplicate_responses_by_date():
            return self._de_duplicate_responses_by_date(updated_responses)
        return updated_responses

    def _drop_responses_from_calculations(
        self,
        violation_responses: List[StateSupervisionViolationResponse],
    ) -> List[StateSupervisionViolationResponse]:
        """Filters out responses with null dates or that are drafts"""
        filtered_responses = [
            response
            for response in violation_responses
            if response.response_date is not None and not response.is_draft
        ]
        return filtered_responses

    def _sorted_violation_responses(
        self,
        violation_responses: List[StateSupervisionViolationResponse],
    ) -> List[StateSupervisionViolationResponse]:
        """Sorts the list of |violation_responses|."""
        # All responses will have a response_date at this point, but date.min helps
        # to satisfy mypy
        violation_responses.sort(key=lambda b: b.response_date or datetime.date.min)

        return violation_responses

    def _de_duplicate_responses_by_date(
        self,
        violation_responses: List[StateSupervisionViolationResponse],
    ) -> List[StateSupervisionViolationResponse]:
        """Some states may erroneously have multiple violation responses with the
        same `response_date` that require de-duplication. To avoid over-counting
        violation responses for these states, we collapse all violation types listed
        on the violations for responses with the same response_date.
        """
        bucketed_responses_by_date: Dict[
            datetime.date, List[StateSupervisionViolationResponse]
        ] = defaultdict(list)
        for response in violation_responses:
            if not response.response_date:
                continue
            bucketed_responses_by_date[response.response_date].append(response)

        deduped_responses_by_date: Dict[
            datetime.date, StateSupervisionViolationResponse
        ] = {}
        for response_date, responses in bucketed_responses_by_date.items():
            updated_response = responses[0]
            seen_violation_types: Set[StateSupervisionViolationType] = set()
            deduped_violation_type_entries: List[
                StateSupervisionViolationTypeEntry
            ] = []
            for response in responses:
                if response.supervision_violation is None:
                    # If this response has no violation then there is no information
                    # we need from it
                    continue
                for (
                    violation_type_entry
                ) in response.supervision_violation.supervision_violation_types:
                    if violation_type_entry.violation_type is None:
                        continue
                    if violation_type_entry.violation_type not in seen_violation_types:
                        deduped_violation_type_entries.append(violation_type_entry)
                        seen_violation_types.add(violation_type_entry.violation_type)

            updated_response.supervision_violation = attr.evolve(
                updated_response.supervision_violation,
                supervision_violation_types=list(deduped_violation_type_entries),
            )
            deduped_responses_by_date[response_date] = updated_response

        return list(deduped_responses_by_date.values())

    def _update_violations_on_responses(
        self,
        violation_responses: List[StateSupervisionViolationResponse],
    ) -> List[StateSupervisionViolationResponse]:
        """For the violation on each response, adds additional violation types to the
        list of supervision_violation_types and performs necessary updates to the
        violated conditions. The state-specific delegates determine whether or not
        additional violation types need to be added, as well as the necessary updates
        needed to be performed on StateSupervisionViolatedConditionEntry entities
        associated with a given StateSupervisionViolationResponse.

        By default, no additional violation types are added and no updates are made
        to the violated conditions."""

        updated_responses = []
        for response in violation_responses:
            updated_supervision_violation: Optional[StateSupervisionViolation] = None

            if response.supervision_violation:
                additional_types = (
                    self.delegate.get_additional_violation_types_for_response(response)
                )

                supervision_violation = response.supervision_violation

                updated_violation_types = (
                    supervision_violation.supervision_violation_types
                )
                updated_violation_types.extend(additional_types)

                updated_conditions: List[StateSupervisionViolatedConditionEntry] = []

                for condition in supervision_violation.supervision_violated_conditions:
                    updated_conditions.append(
                        self.delegate.update_condition(response, condition)
                    )

                updated_supervision_violation = attr.evolve(
                    supervision_violation,
                    supervision_violation_types=updated_violation_types,
                    supervision_violated_conditions=updated_conditions,
                )

            updated_response = attr.evolve(
                response,
                supervision_violation=updated_supervision_violation,
            )

            updated_responses.append(updated_response)
        return updated_responses