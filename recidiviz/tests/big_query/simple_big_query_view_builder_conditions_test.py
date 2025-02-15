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
"""Implements tests for conditions on SimpleBigQueryViewBuilder."""
from unittest import TestCase, mock

from recidiviz.big_query.big_query_view import SimpleBigQueryViewBuilder


class TestSimpleBigQueryViewBuilderConditions(TestCase):
    """Tests for conditions on SimpleBigQueryViewBuilder."""

    def setUp(self) -> None:
        self.metadata_patcher = mock.patch("recidiviz.utils.metadata.project_id")
        self.mock_project_id_fn = self.metadata_patcher.start()
        self.mock_project_id_fn.return_value = "test-project"

    def tearDown(self) -> None:
        self.metadata_patcher.stop()

    def test_should_not_deploy(self) -> None:
        builder = SimpleBigQueryViewBuilder(
            dataset_id="fake_dataset",
            view_id="my_fake_view",
            description="my_fake_view description",
            view_query_template="SELECT NULL LIMIT 0",
            should_deploy_predicate=(lambda: False),
        )
        view = builder.build()
        self.assertFalse(view.should_deploy())

    def test_should_deploy(self) -> None:
        builder = SimpleBigQueryViewBuilder(
            dataset_id="fake_dataset",
            view_id="my_fake_view",
            description="my_fake_view description",
            view_query_template="SELECT NULL LIMIT 0",
            should_deploy_predicate=(lambda: True),
        )

        view = builder.build()
        self.assertTrue(view.should_deploy())

    def test_should_deploy_default(self) -> None:
        builder = SimpleBigQueryViewBuilder(
            dataset_id="fake_dataset",
            view_id="my_fake_view",
            description="my_fake_view description",
            view_query_template="SELECT NULL LIMIT 0",
        )

        view = builder.build()
        self.assertTrue(view.should_deploy())
