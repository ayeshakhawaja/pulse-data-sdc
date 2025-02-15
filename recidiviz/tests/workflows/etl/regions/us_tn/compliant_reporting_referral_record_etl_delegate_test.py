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
"""Tests the ability for CompliantReportingReferralRecordEtlDelegate to parse json rows."""
import os
from datetime import datetime, timezone
from unittest import TestCase, mock
from unittest.mock import MagicMock, patch

from freezegun import freeze_time

from recidiviz.tests.workflows.etl.workflows_firestore_etl_delegate_test import (
    FakeFileStream,
)
from recidiviz.utils.metadata import local_project_id_override
from recidiviz.workflows.etl.regions.us_tn.compliant_reporting_referral_record_etl_delegate import (
    CompliantReportingReferralRecordETLDelegate,
)


class CompliantReportingReferralRecordEtlDelegateTest(TestCase):
    """
    Test class for the CompliantReportingReferralRecordETLDelegate
    """

    def test_transform_row(self) -> None:
        """
        Test that the transform_row method correctly parses the json
        """
        delegate = CompliantReportingReferralRecordETLDelegate()

        path_to_fixture = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "fixtures",
            "compliant_reporting_referral_record.json",
        )
        with open(path_to_fixture, "r", encoding="utf-8") as fp:
            fixture = fp.readline()
            doc_id, row = delegate.transform_row(fixture)
            self.assertEqual(doc_id, "200")
            self.assertEqual(
                row,
                {
                    "stateCode": "US_XX",
                    "poFirstName": "Joey",
                    "poLastName": "Joe",
                    "clientFirstName": "Matilda",
                    "clientLastName": "Mouse",
                    "dateToday": "2022-03-25",
                    "tdocId": "200",
                    "physicalAddress": "123 fake st., Metropolis, TN 59545",
                    "convictionCounty": "123ABC",
                    "currentOffenses": ["BURGLARY", "AGGRAVATED BURGLARY"],
                    "finesFeesEligible": "regular_payments",
                    "judicialDistrict": None,
                    "lifetimeOffensesExpired": None,
                    "pastOffenses": None,
                    "drugScreensPastYear": [
                        {"date": "2021-02-03", "result": "DRUN"},
                        {"date": "2021-04-20", "result": "DRUN"},
                    ],
                    "eligibilityCategory": "c1",
                    "remainingCriteriaNeeded": 3,
                    "sanctionsPastYear": None,
                    "supervisionType": "TN PROBATIONER",
                    "sentenceStartDate": "2020-01-01",
                    "sentenceLengthDays": "1000",
                    "expirationDate": "2024-01-01",
                    "supervisionFeeAssessed": "1000.0",
                    "supervisionFeeArrearaged": True,
                    "supervisionFeeArrearagedAmount": "1138.0",
                    "supervisionFeeExemptionType": [],
                    "courtCostsPaid": False,
                    "restitutionAmt": "200.0",
                    "restitutionMonthlyPayment": "0.0",
                    "restitutionMonthlyPaymentTo": ["SEE ORDER IN FILE"],
                    "specialConditionsAlcDrugScreen": False,
                    "specialConditionsAlcDrugScreenDate": "2022-02-18",
                    "specialConditionsAlcDrugAssessmentComplete": False,
                    "specialConditionsAlcDrugTreatment": False,
                    "specialConditionsAlcDrugTreatmentCurrent": False,
                    "specialConditionsCounseling": False,
                    "specialConditionsCounselingAngerManagementCurrent": False,
                    "specialConditionsCommunityService": False,
                    "specialConditionsCommunityServiceCurrent": False,
                    "specialConditionsProgramming": False,
                    "specialConditionsProgrammingCognitiveBehavior": False,
                    "specialConditionsProgrammingCognitiveBehaviorCurrent": False,
                    "specialConditionsProgrammingSafe": False,
                    "specialConditionsProgrammingSafeCurrent": False,
                    "specialConditionsProgrammingVictimImpact": False,
                    "specialConditionsProgrammingVictimImpactCurrent": False,
                    "specialConditionsProgrammingFsw": False,
                    "specialConditionsProgrammingFswCurrent": False,
                },
            )

            fixture = fp.readline()
            doc_id, row = delegate.transform_row(fixture)
            self.assertEqual(doc_id, "201")
            self.assertEqual(
                row,
                {
                    "stateCode": "US_XX",
                    "poFirstName": "Sally",
                    "poLastName": "Slithers",
                    "clientFirstName": "Harry",
                    "clientLastName": "",
                    "dateToday": "2022-03-25",
                    "tdocId": "201",
                    "currentEmployer": "WAIVER",
                    "driversLicense": "12345",
                    "drugScreensPastYear": [],
                    "eligibilityCategory": "c2",
                    "finesFeesEligible": "regular_payments",
                    "judicialDistrict": None,
                    "lifetimeOffensesExpired": None,
                    "pastOffenses": None,
                    "currentOffenses": ["THEFT"],
                    "remainingCriteriaNeeded": 0,
                    "sanctionsPastYear": None,
                    "zeroToleranceCodes": [
                        {"contactNoteDate": "2020-02-02", "contactNoteType": "COHC"},
                        {"contactNoteDate": "2020-03-03", "contactNoteType": "PWAR"},
                    ],
                    "supervisionType": "TN PAROLEE",
                    "supervisionFeeAssessed": "0.0",
                    "supervisionFeeArrearaged": False,
                    "supervisionFeeArrearagedAmount": "0.0",
                    "supervisionFeeExemptionType": ["SSDB", "SSDB"],
                    "supervisionFeeWaived": "Fees Waived",
                    "courtCostsPaid": False,
                    "specialConditionsAlcDrugScreen": False,
                    "specialConditionsAlcDrugAssessmentComplete": False,
                    "specialConditionsAlcDrugTreatment": False,
                    "specialConditionsAlcDrugTreatmentCurrent": False,
                    "specialConditionsCounseling": False,
                    "specialConditionsCounselingAngerManagementCurrent": False,
                    "specialConditionsCommunityService": False,
                    "specialConditionsCommunityServiceCurrent": False,
                    "specialConditionsProgramming": False,
                    "specialConditionsProgrammingCognitiveBehavior": False,
                    "specialConditionsProgrammingCognitiveBehaviorCurrent": False,
                    "specialConditionsProgrammingSafe": False,
                    "specialConditionsProgrammingSafeCurrent": False,
                    "specialConditionsProgrammingVictimImpact": False,
                    "specialConditionsProgrammingVictimImpactCurrent": False,
                    "specialConditionsProgrammingFsw": False,
                    "specialConditionsProgrammingFswCurrent": False,
                },
            )

            fixture = fp.readline()
            doc_id, row = delegate.transform_row(fixture)
            self.assertEqual(doc_id, "202")
            self.assertEqual(
                row,
                {
                    "stateCode": "US_XX",
                    "poFirstName": "TEST",
                    "poLastName": "OFFICER1",
                    "clientFirstName": "TONYE",
                    "clientLastName": "THOMPSON",
                    "dateToday": "2022-03-25",
                    "tdocId": "202",
                    "drugScreensPastYear": [],
                    "eligibilityCategory": "c3",
                    "finesFeesEligible": "low_balance",
                    "judicialDistrict": None,
                    "lifetimeOffensesExpired": None,
                    "pastOffenses": None,
                    "remainingCriteriaNeeded": 1,
                    "sanctionsPastYear": None,
                    "currentOffenses": ["FAILURE TO APPEAR (FELONY)"],
                    "supervisionType": "TN PROBATIONER",
                    "supervisionFeeAssessed": "",
                    "supervisionFeeArrearaged": False,
                    "supervisionFeeArrearagedAmount": "",
                    "supervisionFeeExemptionType": ["SSDB", "SSDB"],
                    "courtCostsPaid": False,
                    "specialConditionsAlcDrugScreen": False,
                    "specialConditionsAlcDrugAssessmentComplete": False,
                    "specialConditionsAlcDrugTreatment": False,
                    "specialConditionsAlcDrugTreatmentCurrent": False,
                    "specialConditionsCounseling": False,
                    "specialConditionsCounselingAngerManagementCurrent": False,
                    "specialConditionsCommunityService": False,
                    "specialConditionsCommunityServiceCurrent": False,
                    "specialConditionsProgramming": False,
                    "specialConditionsProgrammingCognitiveBehavior": False,
                    "specialConditionsProgrammingCognitiveBehaviorCurrent": False,
                    "specialConditionsProgrammingSafe": False,
                    "specialConditionsProgrammingSafeCurrent": False,
                    "specialConditionsProgrammingVictimImpact": False,
                    "specialConditionsProgrammingVictimImpactCurrent": False,
                    "specialConditionsProgrammingFsw": False,
                    "specialConditionsProgrammingFswCurrent": False,
                },
            )

    @patch("google.cloud.firestore.Client")
    @patch("recidiviz.firestore.firestore_client.FirestoreClientImpl.get_collection")
    @patch("recidiviz.firestore.firestore_client.FirestoreClientImpl.batch")
    @patch(
        "recidiviz.firestore.firestore_client.FirestoreClientImpl.delete_old_documents"
    )
    @patch(
        "recidiviz.workflows.etl.workflows_etl_delegate.WorkflowsETLDelegate.get_file_stream"
    )
    def test_run_etl(
        self,
        mock_get_file_stream: MagicMock,
        _mock_delete_old_documents: MagicMock,
        mock_batch_writer: MagicMock,
        mock_get_collection: MagicMock,
        _mock_firestore_client: MagicMock,
    ) -> None:
        """Tests that the ETL Delegate for CompliantReportingReferralRecord imports the collection with the
        document_id."""
        mock_batch_set = MagicMock()
        mock_batch_writer.return_value = mock_batch_set
        mock_get_file_stream.return_value = [FakeFileStream(1)]
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        mock_document_ref = MagicMock()
        mock_collection.document.return_value = mock_document_ref
        mock_now = datetime(2022, 5, 1, tzinfo=timezone.utc)
        document_id = "us_tn_123"
        with local_project_id_override("test-project"):
            with freeze_time(mock_now):
                with mock.patch.object(
                    CompliantReportingReferralRecordETLDelegate, "transform_row"
                ) as mock_transform:
                    mock_transform.return_value = (123, {"personExternalId": 123})
                    delegate = CompliantReportingReferralRecordETLDelegate()
                    delegate.run_etl(
                        "US_TN", "compliant_reporting_referral_record.json"
                    )
                    mock_collection.document.assert_called_once_with(document_id)
                    mock_batch_set.set.assert_called_once_with(
                        mock_document_ref,
                        {
                            "personExternalId": 123,
                            "__loadedAt": mock_now,
                        },
                    )
