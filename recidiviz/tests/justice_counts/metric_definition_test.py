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
"""This class implements tests for Justice Counts Dimension classes."""

from unittest import TestCase

from recidiviz.justice_counts.metrics import law_enforcement
from recidiviz.justice_counts.metrics.metric_registry import METRICS


class TestJusticeCountsMetricDefinition(TestCase):
    """Implements tests for the Justice Counts MetricDefinition class."""

    def test_metric_keys_are_unique(self) -> None:
        metric_keys = [metric.key for metric in METRICS]
        self.assertEqual(len(metric_keys), len(set(metric_keys)))

    def test_law_enforcement_metrics(self) -> None:
        self.assertEqual(
            law_enforcement.annual_budget.key,
            "LAW_ENFORCEMENT_BUDGET__metric/law_enforcement/budget/type",
        )
        self.assertEqual(
            law_enforcement.residents.key,
            "LAW_ENFORCEMENT_POPULATION_metric/population/type:RESIDENTS_global/race_and_ethnicity",
        )