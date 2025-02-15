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

"""Abstract base class that encapsulates report-specific context."""
import inspect
import json
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader, Template

from recidiviz.reporting.context.po_monthly_report.constants import (
    BRAND_STYLES,
    Batch,
    ReportType,
)
from recidiviz.reporting.recipient import Recipient


class ReportContext(ABC):
    """Defines the context for generation and delivery of a single email report to a single recipient,
    for a particular report type."""

    def __init__(self, batch: Batch, recipient: Recipient):
        self.batch = batch
        self.state_code = batch.state_code
        self.recipient = recipient
        self.recipient_data = recipient.data
        self.prepared_data: dict = {}

        self._validate_recipient_has_expected_fields(recipient)

        with open(self.get_properties_filepath(), encoding="utf-8") as properties_file:
            self.properties = json.loads(properties_file.read())

        self.jinja_env = Environment(
            loader=FileSystemLoader(self._get_context_templates_folder()),
            **self.jinja_options,
        )

    @property
    def jinja_options(self) -> Dict[str, Any]:
        return {}

    def get_properties_filepath(self) -> str:
        """Returns the filepath to the context's properties.json file"""
        return os.path.join(
            os.path.dirname(inspect.getfile(self.__class__)), "properties.json"
        )

    @abstractmethod
    def get_required_recipient_data_fields(self) -> List[str]:
        """Specifies keys that must exist within `recipient` in order for the class to be instantiated"""

    def _validate_recipient_has_expected_fields(self, recipient: Recipient) -> None:
        missing_keys = [
            expected_key
            for expected_key in self.get_required_recipient_data_fields()
            if expected_key not in recipient.data.keys()
        ]

        if missing_keys:
            raise KeyError(
                f"Missing key(s) {missing_keys} not found in recipient.", recipient
            )

    @abstractmethod
    def get_report_type(self) -> ReportType:
        """Returns the report type for this report."""

    @property
    @abstractmethod
    def html_template(self) -> Template:
        """Returns the context's html template"""

    def get_batch_id(self) -> str:
        """Returns the batch_id for the report context"""
        return self.batch.batch_id

    def get_email_address(self) -> str:
        """Returns the email_address to use to generate the filenames for email delivery."""
        return self.recipient.email_address

    def get_prepared_data(self) -> dict:
        """Execute report-specific rules that process the recipient data before templating, returning the prepared,
        report-ready template values.
        This is guaranteed to return the prepared data at any point in the instance's lifecycle. If the data has never
        been prepared before, self.prepare_for_generation will be called and its value set on this instance. If it has
        been called before, its value will be returned straight-away.
        """
        if self.prepared_data:
            prepared_data = self.prepared_data
        else:
            prepared_data = self._prepare_for_generation()

        # add data common to all report types
        if "brand_styles" not in prepared_data:
            prepared_data["brand_styles"] = BRAND_STYLES

        return prepared_data

    def render_html(self, minify: bool = True) -> str:
        """Interpolates the report's prepared data into the template
        Returns: Interpolated template"""
        prepared_data = self.get_prepared_data()
        original = self.html_template.render(prepared_data)
        if not minify:
            return original
        soup = BeautifulSoup(original, "html.parser")
        return str(soup).strip()

    @abstractmethod
    def _prepare_for_generation(self) -> dict:
        """Execute report-specific rules that process the recipient data before templating, returning the prepared,
        report-ready template values.
        This will set self.prepared_data on the instance upon completion. It can be called at any time to reset and
        rebuild this instance's prepared data, i.e. it executes regardless of whether it has been invoked previously.
        NOTE: Implementors of this function must set self.prepared_data to the final results of invocation.
        """

    def _get_context_templates_folder(self) -> str:
        return os.path.join(os.path.dirname(__file__), "templates")
