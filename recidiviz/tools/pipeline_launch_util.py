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
"""Util for launching Dataflow pipelines."""
from __future__ import absolute_import

import importlib
import pkgutil
from typing import List, Type

from recidiviz.calculator.pipeline.base_pipeline import (
    BasePipeline,
    PipelineRunDelegate,
)
from recidiviz.calculator.pipeline.utils.pipeline_run_delegate_utils import (
    TOP_LEVEL_PIPELINE_MODULES,
    collect_all_pipeline_run_delegate_classes,
)


def load_all_pipelines() -> None:
    """Loads all subclasses of PipelineRunDelegate."""
    for top_level_pipeline_module in TOP_LEVEL_PIPELINE_MODULES:
        for _, name, _ in pkgutil.walk_packages(top_level_pipeline_module.__path__):  # type: ignore
            full_name = f"{top_level_pipeline_module.__name__}.{name}.pipeline"
            try:
                importlib.import_module(full_name)
            except ModuleNotFoundError:
                continue


def collect_all_pipeline_names() -> List[str]:
    """Collects all of the pipeline names from all of the implementations of the
    PipelineRunDelegate. A PipelineRunDelegate must exist inside one of the modules
    listed in the TOP_LEVEL_PIPELINE_MODULES for it to be included."""
    run_delegates = collect_all_pipeline_run_delegate_classes()

    return [
        run_delegate.pipeline_config().pipeline_name.lower()
        for run_delegate in run_delegates
    ]


def _delegate_cls_for_pipeline_name(pipeline_name: str) -> Type[PipelineRunDelegate]:
    """Finds the PipelineRunDelegate class corresponding to the pipeline with the
    given |pipeline_name|."""
    all_run_delegates = collect_all_pipeline_run_delegate_classes()
    delegates_with_pipeline_name = [
        delegate
        for delegate in all_run_delegates
        if delegate.pipeline_config().pipeline_name.lower() == pipeline_name
    ]

    if len(delegates_with_pipeline_name) != 1:
        raise ValueError(
            "Expected exactly one PipelineRunDelegate with the "
            f"pipeline_name: {pipeline_name}. Found: {delegates_with_pipeline_name}."
        )

    return delegates_with_pipeline_name[0]


def run_pipeline(pipeline_name: str, argv: List[str]) -> None:
    """Runs the given pipeline_module with the arguments contained in argv."""
    delegate_cls = _delegate_cls_for_pipeline_name(pipeline_name)
    pipeline = BasePipeline(pipeline_run_delegate=delegate_cls.build_from_args(argv))
    pipeline.run()
