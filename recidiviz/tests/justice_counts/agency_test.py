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
"""This class implements tests for the Justice Counts AgencyInterface."""


from recidiviz.justice_counts.agency import AgencyInterface
from recidiviz.persistence.database.session_factory import SessionFactory
from recidiviz.tests.justice_counts.utils import JusticeCountsDatabaseTestCase


class TestJusticeCountsQuerier(JusticeCountsDatabaseTestCase):
    """Implements tests for the JusticeCountsQuerier."""

    def test_create_and_get_agencies(self) -> None:
        with SessionFactory.using_database(self.database_key) as session:
            AgencyInterface.create_agency(session=session, name="Agency Alpha")
            AgencyInterface.create_agency(session=session, name="Beta Initiative")

        with SessionFactory.using_database(self.database_key) as session:
            agency_1 = AgencyInterface.get_agency_by_name(
                session=session, name="Agency Alpha"
            )
            self.assertEqual(agency_1.name, "Agency Alpha")

            agencies = AgencyInterface.get_agencies(session=session)
            self.assertEqual(
                {a.name for a in agencies}, {"Agency Alpha", "Beta Initiative"}
            )