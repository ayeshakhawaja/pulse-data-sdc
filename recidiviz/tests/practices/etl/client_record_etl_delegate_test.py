#  Recidiviz - a data platform for criminal justice reform
#  Copyright (C) 2022 Recidiviz, Inc.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
#  =============================================================================
"""Tests the ability for ClientRecordEtlDelegate to parse json rows."""
import os
from datetime import datetime
from unittest import TestCase

from recidiviz.practices.etl.client_record_etl_delegate import ClientRecordETLDelegate


class ClientRecordEtlDelegateTest(TestCase):
    """
    Test class for the ClientRecordEtlDelegate
    """

    def test_transform_row(self) -> None:
        """
        Test that the transform_row method correctly parses the json
        """
        delegate = ClientRecordETLDelegate()

        path_to_fixture = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "fixtures",
            "client_record.json",
        )
        with open(path_to_fixture, "r", encoding="utf-8") as fp:
            fixture = fp.readline()
            doc_id, row = delegate.transform_row(fixture)
            self.assertEqual(doc_id, "200")
            self.assertEqual(
                row,
                {
                    "address": "123 fake st.",
                    "compliantReportingEligible": {
                        "currentOffenses": None,
                        "drugScreensPastYear": [
                            {"date": datetime(2021, 2, 3, 0, 0), "result": "DRUN"},
                            {"date": datetime(2021, 4, 20, 0, 0), "result": "DRUN"},
                        ],
                        "eligibleLevelStart": datetime(2021, 3, 17, 0, 0),
                        "judicialDistrict": "7",
                        "lifetimeOffensesExpired": None,
                        "mostRecentArrestCheck": datetime(2021, 11, 15, 0, 0),
                        "sanctionsPastYear": ["OPRD"],
                    },
                    "currentBalance": 45.1,
                    "eligible": True,
                    "eligibleWithDiscretion": True,
                    "expirationDate": datetime(2022, 2, 28, 0, 0),
                    "feeExemptions": "Exemption 1, Exemption2",
                    "lastPaymentAmount": 10.25,
                    "lastPaymentDate": datetime(2021, 12, 20, 0, 0),
                    "nextSpecialConditionsCheck": datetime(2021, 12, 2, 0, 0),
                    "officerId": "100",
                    "personExternalId": "200",
                    "personName": {
                        "given_names": "Matilda",
                        "middle_names": "",
                        "name_suffix": "",
                        "surname": "Mouse",
                    },
                    "phoneNumber": "8889997777",
                    "specialConditions": "SPECIAL",
                    "stateCode": "US_XX",
                    "supervisionLevel": "MEDIUM",
                    "supervisionLevelStart": datetime(2020, 3, 10, 0, 0),
                    "supervisionType": "PROBATION",
                },
            )

            fixture = fp.readline()
            doc_id, row = delegate.transform_row(fixture)
            self.assertEqual(doc_id, "201")
            self.assertEqual(
                row,
                {
                    "currentBalance": 282,
                    "eligible": False,
                    "eligibleWithDiscretion": False,
                    "officerId": "102",
                    "personExternalId": "201",
                    "personName": {
                        "given_names": "Harry",
                        "middle_names": "Henry",
                        "name_suffix": "",
                        "surname": "Houdini",
                    },
                    "specialConditions": "NONE",
                    "stateCode": "US_XX",
                    "supervisionLevelStart": datetime(1900, 3, 10, 0, 0),
                    "supervisionType": "PAROLE",
                },
            )