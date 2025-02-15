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
# ============================================================================
""" Contains the configuration for which Pathways metrics are enabled """

from typing import Dict, List

from recidiviz.calculator.query.state.views.dashboard.pathways.pathways_enabled_states import (
    get_pathways_enabled_states,
)
from recidiviz.case_triage.pathways.metrics.metric_query_builders import ALL_METRICS
from recidiviz.case_triage.pathways.metrics.query_builders.metric_query_builder import (
    MetricQueryBuilder,
)
from recidiviz.common.constants.states import _FakeStateCode
from recidiviz.persistence.database.schema.pathways.schema import PathwaysBase

# TODO(#13950): Replace with StateCode
ENABLED_METRICS_BY_STATE: Dict[_FakeStateCode, List[MetricQueryBuilder]] = {
    _FakeStateCode(state_code): ALL_METRICS
    for state_code in get_pathways_enabled_states()
}

ENABLED_METRICS_BY_STATE_BY_NAME = {
    state_code: {metric.name: metric for metric in metrics}
    for state_code, metrics in ENABLED_METRICS_BY_STATE.items()
}


def get_metrics_for_entity(db_entity: PathwaysBase) -> List[MetricQueryBuilder]:
    return [metric for metric in ALL_METRICS if metric.model == db_entity]
