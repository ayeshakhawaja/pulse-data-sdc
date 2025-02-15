# Recidiviz - a data platform for criminal justice reform
# Copyright (C) 2019 Recidiviz, Inc.
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
# ============================================================================

"""Converts scraped IngestInfo data to the persistence layer entity."""

import copy
import logging
from abc import abstractmethod
from typing import List

import attr

from recidiviz.common.constants.entity_enum import EnumParsingError
from recidiviz.common.constants.state.state_person import (
    StateEthnicity,
    StateGender,
    StateRace,
)
from recidiviz.common.ingest_metadata import LegacyStateIngestMetadata
from recidiviz.ingest.models.ingest_info_pb2 import IngestInfo
from recidiviz.persistence.entity.entities import EntityPersonType

# TODO(#8905): Remove the State enums once all states have been migrated to v2 ingest
#  mappings.
PROTECTED_CLASSES = (StateRace, StateEthnicity, StateGender)


@attr.s(frozen=True)
class EntityDeserializationResult:
    enum_parsing_errors: int = attr.ib()
    general_parsing_errors: int = attr.ib()
    protected_class_errors: int = attr.ib()
    people: List[EntityPersonType] = attr.ib(factory=list)


class BaseConverter:
    """Base class for all data converters of IngestInfo proto objects."""

    def __init__(self, ingest_info: IngestInfo, metadata: LegacyStateIngestMetadata):
        self.ingest_info = copy.deepcopy(ingest_info)
        self.metadata = metadata

    def run_convert(self) -> EntityDeserializationResult:
        people: List[EntityPersonType] = []
        protected_class_errors = 0
        enum_parsing_errors = 0
        general_parsing_errors = 0
        while not self._is_complete():
            person = self._pop_person()
            try:
                converted_person = self._convert_person(person)
                people.append(converted_person)
            except EnumParsingError as e:
                logging.error(str(e))
                self._compliant_log_person(person)
                if _is_protected_error(e):
                    protected_class_errors += 1
                else:
                    enum_parsing_errors += 1
            except Exception as e:
                logging.error(str(e))
                general_parsing_errors += 1
                raise e

        return EntityDeserializationResult(
            people=people,
            enum_parsing_errors=enum_parsing_errors,
            general_parsing_errors=general_parsing_errors,
            protected_class_errors=protected_class_errors,
        )

    @abstractmethod
    def _pop_person(self):
        """Pops a person from the list of persons to be converted."""

    @abstractmethod
    def _convert_person(self, ingest_person) -> EntityPersonType:
        """Converts the ingested person and all of its children to Entities."""

    @abstractmethod
    def _is_complete(self) -> bool:
        """Returns whether or not we've converted all entities in the
        IngestInfo."""

    @abstractmethod
    def _compliant_log_person(self, ingest_person):
        """Logs the ingested person in a security-compliant manner."""


def _is_protected_error(error):
    return error.entity_type in PROTECTED_CLASSES
