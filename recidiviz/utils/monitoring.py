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
# =============================================================================

"""Creates monitoring client for measuring and recording stats."""
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

from opencensus.ext.stackdriver import stats_exporter as stackdriver
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.tags import TagContext, TagMap


# pylint: disable=protected-access
def stats() -> stats_module._Stats:
    return stats_module.stats


def register_stackdriver_exporter() -> None:
    exporter = stackdriver.new_stats_exporter()
    stats().view_manager.register_exporter(exporter)


def register_views(views: List[view_module.View]) -> None:
    for view in views:
        stats().view_manager.register_view(view)


def set_context_tags(tags: Dict[str, Any]) -> ContextVar:
    tag_map = TagMap(TagContext.get())

    for key, value in tags.items():
        if value:
            tag_map.insert(key, str(value))
        else:
            tag_map.delete(key)

    return TagContext.contextvar.set(tag_map)


def context_tags() -> TagMap:
    """Returns a copy of the context TagMap"""
    tag_map = TagContext.get()
    return TagMap(tag_map.map if tag_map else None)


@contextmanager
def push_tags(tags: Dict[str, Any]) -> TagContext.contextvar:
    token = set_context_tags(tags)
    try:
        yield
    finally:
        TagContext.contextvar.reset(token)


def push_region_tag(
    region_code: str, ingest_instance: Optional[str]
) -> TagContext.contextvar:
    tags = {TagKey.REGION: region_code}
    if ingest_instance is not None:
        tags[TagKey.INGEST_INSTANCE] = ingest_instance
    return push_tags(tags)


def with_region_tag(func: Callable) -> Callable:
    @wraps(func)
    def set_region_tag(
        region_code: str,
        *args: Any,
        ingest_instance: Optional[str] = None,
        **kwargs: Any
    ) -> Any:
        with push_region_tag(region_code, ingest_instance):
            return func(region_code, *args, **kwargs)

    return set_region_tag


@contextmanager
def measurements(tags: Optional[Dict[str, Any]] = None) -> TagContext.contextvar:
    mmap = stats().stats_recorder.new_measurement_map()
    try:
        yield mmap
    finally:
        tag_map = context_tags()
        if tags:
            for key, value in tags.items():
                tag_map.insert(key, str(value))
        mmap.record(tag_map)


def exponential_buckets(start: float, factor: float, count: int) -> List[float]:
    """Creates `count` buckets where `start` is the first bucket's upper boundary, and each subsequent bucket has an
    upper boundary that is `factor` larger.

    E.g. start=10, factor=2, count=5 would create [0, 10, 20, 40, 80, 160]
    """
    buckets = []
    next_boundary = start
    for _ in range(count):
        buckets.append(next_boundary)
        next_boundary *= factor
    return buckets


class TagKey:
    """Scope to hold tag key constants"""

    ENTITY_TYPE = "entity_type"
    ERROR = "error"
    PERSISTED = "persisted"
    REASON = "reason"
    REGION = "region"
    SHOULD_PERSIST = "should_persist"
    STATUS = "status"

    # Ingest related tags
    INGEST_INSTANCE = "ingest_instance"
    INGEST_TASK_TAG = "ingest_task_tag"
    INGEST_VIEW_EXPORT_TAG = "ingest_view_export_tag"
    INGEST_VIEW_MATERIALIZATION_TAG = "ingest_view_materialization_tag"
    RAW_DATA_IMPORT_TAG = "raw_data_import_tag"

    # Bigquery related tags
    VALIDATION_CHECK_TYPE = "validation_check_type"
    VALIDATION_VIEW_ID = "validation_view_id"
    CREATE_UPDATE_VIEWS_NAMESPACE = "create_update_views_namespace"
    CREATE_UPDATE_RAW_DATA_LATEST_VIEWS_FILE_TAG = (
        "create_update_raw_data_latest_views_file_tag"
    )
    METRIC_VIEW_EXPORT_NAME = "metric_view_export_name"
    SFTP_TASK_TYPE = "sftp_task_type"

    # Postgres related tags
    SCHEMA_TYPE = "schema_type"
    DATABASE_NAME = "database_name"

    # Code related tags
    FUNCTION = "function"
    MODULE = "module"
    RECURSION_DEPTH = "recursion_depth"
