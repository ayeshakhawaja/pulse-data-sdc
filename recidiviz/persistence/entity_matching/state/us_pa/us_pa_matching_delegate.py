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
"""Contains logic for US_PA specific entity matching overrides."""

from typing import List, Optional

from recidiviz.common.constants.states import StateCode
from recidiviz.common.ingest_metadata import IngestMetadata
from recidiviz.persistence.database.schema.state import schema
from recidiviz.persistence.entity_matching import entity_matching_utils
from recidiviz.persistence.entity_matching.entity_matching_types import EntityTree
from recidiviz.persistence.entity_matching.state.base_state_matching_delegate import (
    BaseStateMatchingDelegate,
)
from recidiviz.persistence.entity_matching.state.state_matching_utils import (
    nonnull_fields_entity_match,
)


class UsPaMatchingDelegate(BaseStateMatchingDelegate):
    """Class that contains matching logic specific to US_PA."""

    def __init__(self, ingest_metadata: IngestMetadata):
        super().__init__(
            StateCode.US_PA.value.lower(),
            ingest_metadata,
        )

    def get_non_external_id_match(
        self, ingested_entity_tree: EntityTree, db_entity_trees: List[EntityTree]
    ) -> Optional[EntityTree]:
        """PA specific logic to match the |ingested_entity_tree| to one of the
        |db_entity_trees| that does not rely solely on matching by external_id.
        If such a match is found, it is returned.
        """
        if isinstance(
            ingested_entity_tree.entity, (schema.StateAssessment, schema.StateCharge)
        ):
            return entity_matching_utils.get_only_match(
                ingested_entity_tree,
                db_entity_trees,
                field_index=self.field_index,
                matcher=nonnull_fields_entity_match,
            )
        return None
