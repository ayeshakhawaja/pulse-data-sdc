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
"""Domain logic entities for operations database data.

Note: These classes mirror the SQL Alchemy ORM objects but are kept separate. This allows these persistence layer
objects additional flexibility that the SQL Alchemy ORM objects can't provide.
"""

import datetime
from typing import Optional

import attr

from recidiviz.common.attr_mixins import BuildableAttr, DefaultableAttr
from recidiviz.common.constants.operations.direct_ingest_instance_status import (
    DirectIngestStatus,
)
from recidiviz.ingest.direct.types.direct_ingest_instance import DirectIngestInstance
from recidiviz.persistence.entity.base_entity import entity_graph_eq


@attr.s(eq=False)
class OperationsEntity:
    """Base class for all entity types."""

    # Consider Entity abstract and only allow instantiating subclasses
    def __new__(cls, *_, **__):
        if cls is OperationsEntity:
            raise Exception("Abstract class cannot be instantiated")
        return super().__new__(cls)

    def __eq__(self, other):
        return entity_graph_eq(self, other)


@attr.s(eq=False)
class DirectIngestSftpFileMetadata(OperationsEntity, BuildableAttr, DefaultableAttr):
    """Metadata about a file downloaded from SFTP for a particular region."""

    file_id: int = attr.ib()
    region_code: str = attr.ib()
    # The remote file path on the SFTP server
    remote_file_path: str = attr.ib()
    # Time when the file is actually discvoered by the SFTP download controller
    discovery_time: datetime.datetime = attr.ib()
    # Time when we have finished fully processing this file by downloading to the SFTP bucket
    processed_time: Optional[datetime.datetime] = attr.ib()


@attr.s(eq=False)
class DirectIngestRawFileMetadata(OperationsEntity, BuildableAttr, DefaultableAttr):
    """Metadata about a raw file imported directly from a particular region."""

    file_id: int = attr.ib()
    region_code: str = attr.ib()
    # Shortened name for the raw file that corresponds to its YAML schema definition
    file_tag: str = attr.ib()
    # Unprocessed normalized file name for this file, set at time of file discovery.
    normalized_file_name: str = attr.ib()
    # Time when the file is actually discovered by our controller's handle_new_files endpoint.
    discovery_time: datetime.datetime = attr.ib()
    # Time when we have finished fully processing this file by uploading to BQ.
    processed_time: Optional[datetime.datetime] = attr.ib()

    datetimes_contained_upper_bound_inclusive: datetime.datetime = attr.ib()

    @property
    def is_code_table(self) -> bool:
        """Whether or not this file is a code table.

        This means the file does not contain person level data associated with a particular date, but instead
        provides region-specific mappings (e.g. facility names, offense categorizations).
        """
        # TODO(#5935): Fuller support that isn't just based on table prefix.
        return self.file_tag.startswith("RECIDIVIZ_REFERENCE")


@attr.s(eq=False)
class DirectIngestViewMaterializationMetadata(
    OperationsEntity, BuildableAttr, DefaultableAttr
):
    """Represents the metadata known about a job to materialize the results of an ingest
    view and save them for use later in ingest (as rows in a BQ table).
    """

    # The region associated with this materialization job (e.g. 'US_XX')
    region_code: str = attr.ib()

    # The ingest instance associated with this materialization job.
    instance: DirectIngestInstance = attr.ib()

    # Shortened name for the ingest view file that corresponds to its ingest view / YAML
    # mappings definition.
    ingest_view_name: str = attr.ib()

    # The upper bound date used to query data for these particular ingest view results.
    # The results will not contain any data we received after this date.
    upper_bound_datetime_inclusive: datetime.datetime = attr.ib()

    # The lower bound date used to query data for these particular ingest view results.
    # The results will not contain any rows that have remained unmodified with new raw
    # data updates we’ve gotten since this date.
    lower_bound_datetime_exclusive: Optional[datetime.datetime] = attr.ib()

    # Time the materialization job is first scheduled for this view.
    job_creation_time: datetime.datetime = attr.ib()

    # Time the results of this view were materialized (i.e. written to BQ).
    materialization_time: Optional[datetime.datetime] = attr.ib()

    # Whether or not this row is still valid (i.e. it applies to the current ingest
    # rerun).
    is_invalidated: bool = attr.ib()


@attr.s(eq=False)
class DirectIngestInstancePauseStatus(OperationsEntity, BuildableAttr, DefaultableAttr):
    """Status of whether an ingest instance is paused."""

    region_code: str = attr.ib()
    instance: DirectIngestInstance = attr.ib()
    is_paused: bool = attr.ib()


@attr.s(eq=False)
class DirectIngestInstanceStatus(OperationsEntity, BuildableAttr, DefaultableAttr):
    """Status of a direct instance ingest process."""

    # The region code of a particular instance doing ingest.
    region_code: str = attr.ib()

    # The timestamp of when the status of a particular instance changes.
    timestamp: datetime.datetime = attr.ib()

    # The particular instance doing ingest.
    instance: DirectIngestInstance = attr.ib()

    # The status of a particular instance doing ingest.
    status: DirectIngestStatus = attr.ib()
