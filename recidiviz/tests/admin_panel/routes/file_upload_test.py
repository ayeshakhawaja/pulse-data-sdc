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
# =============================================================================
"""Tests for file upload line staff tools route"""
import os
from datetime import date, time
from http import HTTPStatus
from unittest import TestCase
from unittest.mock import MagicMock, patch

import pandas as pd
from flask import Blueprint, Flask
from google.cloud import bigquery
from pandas.testing import assert_frame_equal

from recidiviz.admin_panel.routes.line_staff_tools import add_line_staff_tools_routes

# To modify this file, use Excel or download https://docs.google.com/spreadsheets/d/1W3RWWWxlHP4GB-LUegjw63DdbGEN-mUoIa7y7D2XhQc/edit?usp=sharing
# as an excel file. Don't use Numbers on a Mac because it doesn't let you have a column that's just a time
# (https://support.apple.com/guide/numbers/format-dates-currency-and-more-tan23393f3a/mac)
fixture_path = os.path.join(
    os.path.dirname(__file__),
    "fixtures/file_upload.xlsx",
)


@patch("recidiviz.utils.metadata.project_number", MagicMock(return_value="123456789"))
@patch(
    "recidiviz.utils.validate_jwt.validate_iap_jwt_from_app_engine",
    MagicMock(return_value=("test-user", "test-user@recidiviz.org", None)),
)
class FileUploadEndpointTests(TestCase):
    """TestCase for file upload line staff tools route"""

    def setUp(self) -> None:
        self.project_id = "test-project"
        self.project_id_patcher = patch("recidiviz.utils.metadata.project_id")
        self.project_id_patcher.start().return_value = self.project_id

        self.requires_gae_auth_patcher = patch(
            "recidiviz.admin_panel.routes.line_staff_tools.requires_gae_auth",
            side_effect=lambda route: route,
        )
        self.bq_client_patcher = patch(
            "recidiviz.admin_panel.routes.line_staff_tools.BigQueryClientImpl"
        )
        self.requires_gae_auth_patcher.start()
        self.mock_dataset = bigquery.dataset.DatasetReference(
            self.project_id, "test_dataset"
        )
        self.mock_bq_client = self.bq_client_patcher.start().return_value
        self.mock_bq_client.dataset_ref_for_id.return_value = self.mock_dataset
        self.app = Flask(__name__)

        blueprint = Blueprint("file_upload_test", __name__)
        self.app.config["TESTING"] = True

        self.client = self.app.test_client()

        add_line_staff_tools_routes(blueprint)
        self.app.register_blueprint(blueprint)

    def tearDown(self) -> None:
        self.project_id_patcher.stop()
        self.requires_gae_auth_patcher.stop()
        self.bq_client_patcher.stop()

    def test_upload_raw_files_invalid_state(self) -> None:
        response = self.client.post("/api/line_staff_tools/US_ID/upload_raw_files")
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertEqual(
            response.data,
            b"Raw file uploads are not supported for US_ID",
        )

    def test_upload_raw_files_bad_date_string(self) -> None:
        response = self.client.post(
            "/api/line_staff_tools/US_TN/upload_raw_files",
            data={"dateOfStandards": "20220101"},
        )
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertEqual(
            response.data,
            b"dateOfStandards date must be YYYY-MM-DD formatted, received 20220101",
        )

    def test_upload_raw_files_missing_upload_type(self) -> None:
        response = self.client.post(
            "/api/line_staff_tools/US_TN/upload_raw_files",
            data={
                "dateOfStandards": "2022-01-01",
            },
        )
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertIn(
            b"Standards upload type must be one of",
            response.data,
        )

    def test_upload_raw_files_wrong_upload_type(self) -> None:
        response = self.client.post(
            "/api/line_staff_tools/US_TN/upload_raw_files",
            data={"dateOfStandards": "2022-01-01", "uploadType": "FAKE_UPLOAD_TYPE"},
        )
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertIn(
            b"Standards upload type must be one of",
            response.data,
        )

    def test_upload_raw_files(self) -> None:
        with open(fixture_path, "rb") as f:
            response = self.client.post(
                "/api/line_staff_tools/US_TN/upload_raw_files",
                data={
                    "dateOfStandards": "2022-03-10",
                    "uploadType": "STANDARDS_DUE",
                    "file": f,
                },
            )

        self.assertEqual(response.status_code, HTTPStatus.OK)

        expected_date = date(2022, 3, 10)
        expected_df = pd.DataFrame(
            {
                "string_col": pd.Series([pd.NA, "val a", "val, b"], dtype="string"),
                "_1_int_col": pd.Series([2, 3, 10], dtype="Int64"),
                "_time_col": [time(4, 56), time(12, 34, 56), pd.NaT],
                "date_col": [date(2022, 1, 1), pd.NA, pd.NA],
                "bool_col": [pd.NA, True, False],
                "date_of_standards": [expected_date] * 3,
            }
        )

        self.mock_bq_client.load_into_table_from_dataframe_async.assert_called_once()
        args = self.mock_bq_client.load_into_table_from_dataframe_async.call_args.args
        assert_frame_equal(args[0], expected_df, check_column_type=False)
        self.assertEqual(args[1], self.mock_dataset)
        self.assertEqual(args[2], "us_tn_standards_due")