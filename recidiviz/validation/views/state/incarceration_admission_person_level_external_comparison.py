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

"""A view comparing person-level incarceration admission metrics to the person-level values from external metrics
provided by the state.
"""

from recidiviz.big_query.big_query_view import SimpleBigQueryViewBuilder
from recidiviz.calculator.query.state import dataset_config as state_dataset_config
from recidiviz.utils.environment import GCP_PROJECT_STAGING
from recidiviz.utils.metadata import local_project_id_override
from recidiviz.validation.views import dataset_config

INCARCERATION_ADMISSION_PERSON_LEVEL_EXTERNAL_COMPARISON_VIEW_NAME = (
    "incarceration_admission_person_level_external_comparison"
)

INCARCERATION_ADMISSION_PERSON_LEVEL_EXTERNAL_COMPARISON_DESCRIPTION = """
Comparison of internal and external lists of incarceration admissions.
"""

INCARCERATION_ADMISSION_PERSON_LEVEL_EXTERNAL_COMPARISON_QUERY_TEMPLATE = """
WITH external_data AS (
    -- NOTE: You can replace this part of the query with your own query to test the SELECT query you will use to
    -- generate data to insert into the `incarceration_admission_person_level` table.
    SELECT region_code, person_external_id, admission_date
    FROM `{project_id}.{external_accuracy_dataset}.incarceration_admission_person_level`
), external_data_with_ids AS (
    -- Find the internal person_id for the people in the external data
    SELECT region_code, admission_date, external_data.person_external_id, person_id
    FROM external_data
    LEFT JOIN `{project_id}.{state_base_dataset}.state_person_external_id` all_state_person_ids
    ON region_code = all_state_person_ids.state_code AND external_data.person_external_id = all_state_person_ids.external_id
    -- Limit to 'US_PA_CONT' id_type for US_PA
    AND (region_code != 'US_PA' OR id_type = 'US_PA_CONT')
), internal_data AS (
    SELECT state_code as region_code, person_external_id, person_id, admission_date
    FROM `{project_id}.{materialized_metrics_dataset}.most_recent_incarceration_admission_metrics_included_in_state_population_materialized`
    WHERE admission_reason NOT IN ('TRANSFER', 'STATUS_CHANGE')
    -- Exclude parole revocation admissions for states that have parole board hold admissions --
    AND (state_code NOT IN ('US_ID', 'US_MO', 'US_PA') OR NOT (admission_reason = 'REVOCATION' AND supervision_type = 'PAROLE'))
    AND CASE 
      WHEN state_code = 'US_PA' THEN 
        -- Exclude other admission reasons not included in PA external validation data
        admission_reason != 'SANCTION_ADMISSION'
      ELSE TRUE
    END
), internal_metrics_for_valid_regions_and_dates AS (
    SELECT * FROM
    -- Only compare regions and dates for which we have external validation data
    (SELECT DISTINCT region_code, admission_date FROM external_data)
    LEFT JOIN
    internal_data
    USING (region_code, admission_date)
)
SELECT
    region_code,
    admission_date,
    CAST(external_data.person_id AS STRING) AS external_data_person_id,
    CAST(internal_data.person_id AS STRING) AS internal_data_person_id,
    external_data.person_external_id AS external_data_person_external_id
FROM
    external_data_with_ids external_data
FULL OUTER JOIN
    internal_metrics_for_valid_regions_and_dates internal_data
USING (region_code, admission_date, person_id)
"""

INCARCERATION_ADMISSION_PERSON_LEVEL_EXTERNAL_COMPARISON_VIEW_BUILDER = SimpleBigQueryViewBuilder(
    dataset_id=dataset_config.VIEWS_DATASET,
    view_id=INCARCERATION_ADMISSION_PERSON_LEVEL_EXTERNAL_COMPARISON_VIEW_NAME,
    view_query_template=INCARCERATION_ADMISSION_PERSON_LEVEL_EXTERNAL_COMPARISON_QUERY_TEMPLATE,
    description=INCARCERATION_ADMISSION_PERSON_LEVEL_EXTERNAL_COMPARISON_DESCRIPTION,
    external_accuracy_dataset=dataset_config.EXTERNAL_ACCURACY_DATASET,
    materialized_metrics_dataset=state_dataset_config.DATAFLOW_METRICS_MATERIALIZED_DATASET,
    state_base_dataset=state_dataset_config.STATE_BASE_DATASET,
    should_materialize=True,
)

if __name__ == "__main__":
    with local_project_id_override(GCP_PROJECT_STAGING):
        INCARCERATION_ADMISSION_PERSON_LEVEL_EXTERNAL_COMPARISON_VIEW_BUILDER.build_and_print()
