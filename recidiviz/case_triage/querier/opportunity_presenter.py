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
"""Implements an OpportunityPresenter abstraction which reconciles our knowledge
about opportunities derived from our ETL pipeline with actions taken by POs used
to indicate whether those opportunities are immediately actionable vs. should
be re-surfaced later."""
from datetime import datetime
from typing import Any, Dict, Optional

import pytz

from recidiviz.case_triage.demo_helpers import unconvert_fake_person_id_for_demo_user
from recidiviz.case_triage.opportunities.types import Opportunity
from recidiviz.persistence.database.schema.case_triage.schema import OpportunityDeferral


class OpportunityPresenter:
    """Implements the opportunity presenter abstraction."""

    def __init__(
        self,
        opportunity: Opportunity,
        opportunity_deferral: Optional[OpportunityDeferral],
    ):
        self.opportunity = opportunity
        self.opportunity_deferral = opportunity_deferral

    def is_deferred(self) -> bool:
        return (
            self.opportunity_deferral is not None
            and self.opportunity_deferral.deferred_until.replace(tzinfo=pytz.UTC)
            >= datetime.now(tz=pytz.UTC)
        )

    def to_json(self) -> Dict[str, Any]:
        base = {
            "personExternalId": unconvert_fake_person_id_for_demo_user(
                self.opportunity.person_external_id
            ),
            "stateCode": self.opportunity.state_code,
            "supervisingOfficerExternalId": self.opportunity.supervising_officer_external_id,
            "opportunityType": self.opportunity.opportunity_type,
            "opportunityMetadata": self.opportunity.opportunity_metadata,
        }

        if self.opportunity_deferral is not None and self.is_deferred():
            # TODO(#5708): Check the metadata as well to see if the deferral is
            # still active
            base["deferredUntil"] = self.opportunity_deferral.deferred_until
            base["deferralType"] = self.opportunity_deferral.deferral_type
            base["deferralId"] = self.opportunity_deferral.deferral_id
        return base
