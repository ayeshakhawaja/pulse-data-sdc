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
"""All views needed for the population projection simulation"""
from typing import List

from recidiviz.big_query.big_query_view import SimpleBigQueryViewBuilder
from recidiviz.calculator.query.state.views.population_projection.incarceration_remaining_sentences import (
    INCARCERATION_REMAINING_SENTENCES_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.population_projection.microsim_projected_transitions import (
    MICROSIM_PROJECTED_TRANSITIONS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.population_projection.microsim_projection import (
    MICROSIM_PROJECTION_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.population_projection.population_outflows import (
    POPULATION_OUTFLOWS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.population_projection.population_projection_outputs import (
    POPULATION_PROJECTION_OUTPUT_VIEW_BUILDERS,
)
from recidiviz.calculator.query.state.views.population_projection.population_projection_sessions import (
    POPULATION_PROJECTION_SESSIONS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.population_projection.population_transitions import (
    POPULATION_TRANSITIONS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.population_projection.remaining_sentences import (
    REMAINING_SENTENCES_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.population_projection.simulation_run_dates import (
    SIMULATION_RUN_DATES_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.population_projection.supervision_remaining_sentences import (
    SUPERVISION_REMAINING_SENTENCES_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.population_projection.total_population import (
    TOTAL_POPULATION_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.population_projection.us_id.us_id_excluded_population import (
    US_ID_EXCLUDED_POPULATION_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.population_projection.us_id.us_id_monthly_paid_incarceration_population import (
    US_ID_MONTHLY_PAID_INCARCERATION_POPULATION_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.population_projection.us_id.us_id_non_bias_full_population_transitions import (
    US_ID_PAROLE_BOARD_HOLD_FULL_TRANSITIONS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.population_projection.us_id.us_id_parole_board_hold_population_transitions import (
    US_ID_PAROLE_BOARD_HOLD_POPULATION_TRANSITIONS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.population_projection.us_id.us_id_rider_pbh_remaining_sentences import (
    US_ID_RIDER_PBH_REMAINING_SENTENCES_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.population_projection.us_id.us_id_rider_population_transitions import (
    US_ID_RIDER_POPULATION_TRANSITIONS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.population_projection.us_id.us_id_total_jail_population import (
    US_ID_TOTAL_JAIL_POPULATION_VIEW_BUILDER,
)

POPULATION_PROJECTION_VIEW_BUILDERS: List[SimpleBigQueryViewBuilder] = [
    SIMULATION_RUN_DATES_VIEW_BUILDER,  # all input views depend on this view so it must be first in the list
    POPULATION_PROJECTION_SESSIONS_VIEW_BUILDER,
    US_ID_MONTHLY_PAID_INCARCERATION_POPULATION_VIEW_BUILDER,
    POPULATION_OUTFLOWS_VIEW_BUILDER,
    US_ID_PAROLE_BOARD_HOLD_POPULATION_TRANSITIONS_VIEW_BUILDER,
    US_ID_RIDER_POPULATION_TRANSITIONS_VIEW_BUILDER,
    US_ID_RIDER_PBH_REMAINING_SENTENCES_VIEW_BUILDER,
    US_ID_PAROLE_BOARD_HOLD_FULL_TRANSITIONS_VIEW_BUILDER,
    POPULATION_TRANSITIONS_VIEW_BUILDER,
    INCARCERATION_REMAINING_SENTENCES_VIEW_BUILDER,
    SUPERVISION_REMAINING_SENTENCES_VIEW_BUILDER,
    REMAINING_SENTENCES_VIEW_BUILDER,
    TOTAL_POPULATION_VIEW_BUILDER,
    US_ID_TOTAL_JAIL_POPULATION_VIEW_BUILDER,
    US_ID_EXCLUDED_POPULATION_VIEW_BUILDER,
    MICROSIM_PROJECTION_VIEW_BUILDER,
    MICROSIM_PROJECTED_TRANSITIONS_VIEW_BUILDER,
] + POPULATION_PROJECTION_OUTPUT_VIEW_BUILDERS
