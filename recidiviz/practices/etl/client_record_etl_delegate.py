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
"""Delegate class to ETL client records for practices into Firestore."""
import json
import logging
from datetime import datetime
from typing import Tuple

from recidiviz.practices.etl.practices_etl_delegate import PracticesFirestoreETLDelegate
from recidiviz.utils.environment import GCP_PROJECT_STAGING
from recidiviz.utils.metadata import local_project_id_override


class ClientRecordETLDelegate(PracticesFirestoreETLDelegate):
    """Delegate class to ETL the client_record.json file into Firestore."""

    EXPORT_FILENAME = "client_record.json"
    COLLECTION_NAME = "clients"

    def transform_row(self, row: str) -> Tuple[str, dict]:
        data = json.loads(row)

        # First fill the non-nullable fields
        new_document = {
            "personExternalId": data["person_external_id"],
            "stateCode": data["state_code"],
            "personName": json.loads(data["person_name"]),
            "officerId": data["officer_id"],
            "supervisionType": data["supervision_type"],
            "eligible": data["eligible"],
            "eligibleWithDiscretion": data["eligible_with_discretion"],
            "currentBalance": data["current_balance"],
            "specialConditions": data["special_conditions"],
        }

        # add nullable fields
        if "fee_exemptions" in data:
            new_document["feeExemptions"] = data["fee_exemptions"]

        if "phone_number" in data:
            new_document["phoneNumber"] = data["phone_number"]

        if "address" in data:
            new_document["address"] = data["address"]

        if "last_payment_amount" in data:
            new_document["lastPaymentAmount"] = data["last_payment_amount"]

        if "supervision_level" in data:
            new_document["supervisionLevel"] = data["supervision_level"]

        # add nullable dates
        if "supervision_level_start" in data:
            new_document["supervisionLevelStart"] = datetime.fromisoformat(
                data["supervision_level_start"]
            )

        if "next_special_conditions_check" in data:
            new_document["nextSpecialConditionsCheck"] = datetime.fromisoformat(
                data["next_special_conditions_check"]
            )

        if "last_payment_date" in data:
            new_document["lastPaymentDate"] = datetime.fromisoformat(
                data["last_payment_date"]
            )

        if "expiration_date" in data:
            new_document["expirationDate"] = datetime.fromisoformat(
                data["expiration_date"]
            )

        # add nullable objects
        if data["eligible_with_discretion"]:
            new_document["compliantReportingEligible"] = {
                "currentOffenses": data.get("current_offenses"),
                "lifetimeOffensesExpired": data.get("lifetime_offenses_expired"),
                "judicialDistrict": data.get("judicial_district"),
                "drugScreensPastYear": [
                    {
                        "result": screen["ContactNoteType"],
                        "date": datetime.fromisoformat(screen["contact_date"]),
                    }
                    for screen in data["drug_screens_past_year"]
                ],
                "sanctionsPastYear": data.get("sanctions_past_year"),
            }

            if "eligible_level_start" in data:
                new_document["compliantReportingEligible"][
                    "eligibleLevelStart"
                ] = datetime.fromisoformat(data["eligible_level_start"])

            if "most_recent_arrest_check" in data:
                new_document["compliantReportingEligible"][
                    "mostRecentArrestCheck"
                ] = datetime.fromisoformat(data["most_recent_arrest_check"])

        return data["person_external_id"], new_document


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    with local_project_id_override(GCP_PROJECT_STAGING):
        ClientRecordETLDelegate().run_etl()