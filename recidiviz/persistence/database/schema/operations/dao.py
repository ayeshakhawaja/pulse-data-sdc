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
"""Data Access Object (DAO) with logic for accessing operations DB information from a SQL Database."""
import datetime
from typing import List, Optional

from more_itertools import one
from sqlalchemy import case, func

from recidiviz.cloud_storage.gcsfs_path import GcsfsFilePath
from recidiviz.ingest.direct.metadata.direct_ingest_file_metadata_manager import (
    DirectIngestRawFileMetadataSummary,
)
from recidiviz.ingest.direct.types.direct_ingest_instance import DirectIngestInstance
from recidiviz.persistence.database.schema.operations import schema
from recidiviz.persistence.database.session import Session


# TODO(#14198): move operations/dao.py functionality into DirectIngestRawFileMetadataManager and migrate tests
# to postgres_direct_ingest_file_metadata_manager_test.
def get_raw_file_metadata_row_for_path(
    session: Session,
    region_code: str,
    path: GcsfsFilePath,
    raw_data_instance: DirectIngestInstance,
) -> schema.DirectIngestRawFileMetadata:
    """Returns metadata information for the provided path, throws if it doesn't exist."""
    results = (
        session.query(schema.DirectIngestRawFileMetadata)
        .filter_by(
            region_code=region_code.upper(),
            normalized_file_name=path.file_name,
            is_invalidated=False,
            raw_data_instance=raw_data_instance.value,
        )
        .all()
    )

    if len(results) != 1:
        raise ValueError(
            f"Unexpected number of metadata results for path {path.abs_path()}: [{len(results)}]"
        )

    return one(results)


def get_raw_file_metadata_for_file_id(
    session: Session,
    region_code: str,
    file_id: int,
    raw_data_instance: DirectIngestInstance,
) -> schema.DirectIngestRawFileMetadata:
    """Returns metadata information for the provided file id. Throws if it doesn't exist."""
    results = (
        session.query(schema.DirectIngestRawFileMetadata)
        .filter_by(
            region_code=region_code.upper(),
            file_id=file_id,
            raw_data_instance=raw_data_instance.value,
        )
        .all()
    )

    if len(results) != 1:
        raise ValueError(
            f"Unexpected number of metadata results for file_id={file_id}, region_code={region_code.upper()}: "
            f"[{len(results)}]"
        )

    return one(results)


def mark_raw_file_as_invalidated(
    session: Session,
    region_code: str,
    file_id: int,
    raw_data_instance: DirectIngestInstance,
) -> None:
    """Marks the specified row associated with the file_id as invalidated."""
    metadata = get_raw_file_metadata_for_file_id(
        session, region_code, file_id, raw_data_instance
    )
    metadata.is_invalidated = True


def get_sftp_file_metadata_row_for_path(
    session: Session, region_code: str, remote_file_path: str
) -> schema.DirectIngestSftpFileMetadata:
    """Returns metadata information for the provided path, throws if it doesn't exist."""
    results = (
        session.query(schema.DirectIngestSftpFileMetadata)
        .filter_by(region_code=region_code.upper(), remote_file_path=remote_file_path)
        .all()
    )

    if len(results) != 1:
        raise ValueError(
            f"Unexpected number of metadata results for path {remote_file_path}: [{len(results)}]"
        )

    return one(results)


def get_metadata_for_raw_files_discovered_after_datetime(
    session: Session,
    region_code: str,
    raw_file_tag: str,
    discovery_time_lower_bound_exclusive: Optional[datetime.datetime],
    raw_data_instance: DirectIngestInstance,
) -> List[schema.DirectIngestRawFileMetadata]:
    """Returns metadata for all raw files with a given tag that have been updated after the provided date."""

    query = session.query(schema.DirectIngestRawFileMetadata).filter_by(
        region_code=region_code.upper(),
        file_tag=raw_file_tag,
        is_invalidated=False,
        raw_data_instance=raw_data_instance.value,
    )
    if discovery_time_lower_bound_exclusive:
        query = query.filter(
            schema.DirectIngestRawFileMetadata.discovery_time
            > discovery_time_lower_bound_exclusive
        )

    return query.all()


def get_all_raw_file_metadata_rows_for_region(
    session: Session,
    region_code: str,
    raw_data_instance: DirectIngestInstance,
) -> List[DirectIngestRawFileMetadataSummary]:
    """Returns all operations DB raw file metadata rows for the given region."""
    results = (
        session.query(
            schema.DirectIngestRawFileMetadata.file_tag.label("file_tag"),
            func.count(1)
            .filter(schema.DirectIngestRawFileMetadata.processed_time.isnot(None))
            .label("num_processed_files"),
            func.count(1)
            .filter(schema.DirectIngestRawFileMetadata.processed_time.is_(None))
            .label("num_unprocessed_files"),
            func.max(schema.DirectIngestRawFileMetadata.processed_time).label(
                "latest_processed_time"
            ),
            func.max(schema.DirectIngestRawFileMetadata.discovery_time).label(
                "latest_discovery_time"
            ),
            func.max(
                case(
                    [
                        (
                            schema.DirectIngestRawFileMetadata.processed_time.is_(None),
                            None,
                        )
                    ],
                    else_=schema.DirectIngestRawFileMetadata.datetimes_contained_upper_bound_inclusive,
                )
            ).label("latest_processed_datetimes_contained_upper_bound_inclusive"),
        )
        .filter_by(
            region_code=region_code.upper(),
            is_invalidated=False,
            raw_data_instance=raw_data_instance.value,
        )
        .group_by(schema.DirectIngestRawFileMetadata.file_tag)
        .all()
    )
    return [
        DirectIngestRawFileMetadataSummary(
            file_tag=result.file_tag,
            num_processed_files=result.num_processed_files,
            num_unprocessed_files=result.num_unprocessed_files,
            latest_processed_time=result.latest_processed_time,
            latest_discovery_time=result.latest_discovery_time,
            latest_processed_datetimes_contained_upper_bound_inclusive=result.latest_processed_datetimes_contained_upper_bound_inclusive
            if not isinstance(
                result.latest_processed_datetimes_contained_upper_bound_inclusive, str
            )
            else datetime.datetime.fromisoformat(
                result.latest_processed_datetimes_contained_upper_bound_inclusive
            ),
        )
        for result in results
    ]
