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
"""View tracking metrics at the officer level"""
from typing import List, Tuple

from recidiviz.big_query.big_query_view import SimpleBigQueryViewBuilder
from recidiviz.calculator.query.state.dataset_config import ANALYST_VIEWS_DATASET
from recidiviz.utils.environment import GCP_PROJECT_STAGING
from recidiviz.utils.metadata import local_project_id_override


# function for getting view name, description, and query template
def get_view_strings_by_level(level: str) -> Tuple[str, str, str]:
    """
    Takes on input: the level of the metrics dataframe, i.e. one of:
        "officer", "office", or "district".

    Returns a list with three strings:
    1. view name
    2. view description
    3. query template
    """

    if level not in ["officer", "office", "district"]:
        raise ValueError("`level` must be 'officer', 'office', or 'district'.")

    view_id = f"supervision_{level}_metrics"

    view_description = f"""
Tracks {level} level metrics over monthly, quarterly, and yearly scales.

Note that status metrics (e.g. days_incarcerated_1yr) are for all clients assigned
to the {level} in the time period between start_date and end_date and tracked
in the year following assignment.
"""

    # level-dependent columns/metrics
    if level == "officer":
        index_cols = "supervising_officer_external_id"
        level_dependent_metrics = """
        # Officer-specific metrics
        COUNT(DISTINCT district) AS officer_district_count,
        COUNT(DISTINCT office) AS officer_office_count,
        MIN(officer_tenure_days) AS officer_tenure_days,"""
        officer_attributes = """
    MAX(primary_offices.district) AS primary_district,
    MAX(primary_offices.office) AS primary_office,
    AVG(officer_district_count) AS avg_district_count,
    AVG(officer_office_count) AS avg_office_count,
    MIN(officer_tenure_days) AS officer_tenure_days_start,"""

    else:
        if level == "office":
            index_cols = "district, office"
        else:
            index_cols = "district"
        level_dependent_metrics = f"""
        # count/avg/sum across officers with any clients in that {level}
        COUNT(supervising_officer_external_id) AS officer_count,
        AVG(officer_tenure_days) AS officer_tenure_days,
        SAFE_DIVIDE(SUM(officer_tenure_days * caseload_all), SUM(caseload_all))
            AS client_weighted_officer_tenure_days,"""
        officer_attributes = """
    COUNT(DISTINCT primary_offices.supervising_officer_external_id) AS distinct_primary_officers,
    AVG(officer_count) AS avg_officer_count,
    AVG(officer_tenure_days) AS avg_officer_tenure_days,
    AVG(client_weighted_officer_tenure_days) AS avg_client_weighted_officer_tenure_days,"""

    query_template = f"""
/*{{description}}*/
    
WITH date_range AS (
    SELECT
        date,
    FROM
        UNNEST(GENERATE_DATE_ARRAY(
            (
                SELECT MIN(date) 
                FROM `{{project_id}}.{{analyst_dataset}}.supervision_officer_office_metrics_materialized`
            ),
            (
                SELECT MAX(date) 
                FROM `{{project_id}}.{{analyst_dataset}}.supervision_officer_office_metrics_materialized`
            ),
            INTERVAL 1 DAY
        )) AS date
)

, truncated_dates AS (
    SELECT DISTINCT
        "MONTH" AS period,
        DATE_TRUNC(date, MONTH) AS start_date,
        DATE_ADD(DATE_TRUNC(date, MONTH), INTERVAL 1 MONTH) AS end_date,
    FROM
        date_range 
        
    UNION ALL
    
    SELECT DISTINCT
        "QUARTER" AS period,
        DATE_TRUNC(date, QUARTER) AS start_date,
        DATE_ADD(DATE_TRUNC(date, QUARTER), INTERVAL 1 QUARTER) AS end_date,
    FROM
        date_range 
        
    UNION ALL
    
    SELECT DISTINCT
        "YEAR" AS period,
        DATE_TRUNC(date, YEAR) AS start_date,
        DATE_ADD(DATE_TRUNC(date, YEAR), INTERVAL 1 YEAR) AS end_date,
    FROM
        date_range 
)

, primary_offices AS (
    SELECT
        state_code,
        supervising_officer_external_id,
        period,
        start_date,
        end_date,
        district,
        office,
        AVG(IFNULL(caseload_all, 0)) AS avg_daily_caseload_primary,
    FROM
        `{{project_id}}.{{analyst_dataset}}.supervision_officer_office_metrics_materialized` a
    INNER JOIN
        truncated_dates b
    ON
        a.date BETWEEN b.start_date AND b.end_date
    GROUP BY 1, 2, 3, 4, 5, 6, 7
    QUALIFY
        ROW_NUMBER() OVER (PARTITION BY state_code, supervising_officer_external_id, 
            period, start_date, end_date 
            ORDER BY avg_daily_caseload_primary DESC, district, office
        ) = 1
)

# {level}-day
, {level}_level_metrics AS (
    SELECT
        # index
        state_code,
        {index_cols},
        date,
        {level_dependent_metrics}
        # TODO(#11903): compare office and district-level metrics calculated here, which
        # weigh clients by number of officers, to those that weigh all clients
        # equally regardless of PO count.
        
        # sum within {level} on `date`
        SUM(caseload_all) AS caseload_all,
        SUM(caseload_out_of_state) AS caseload_out_of_state,
        SUM(caseload_parole) AS caseload_parole,
        SUM(caseload_probation) AS caseload_probation,
        SUM(caseload_other_supervision_type) AS caseload_other_supervision_type,
        SUM(caseload_female) AS caseload_female,
        SUM(caseload_nonwhite) AS caseload_nonwhite,
        SUM(caseload_general) AS caseload_general,
        SUM(caseload_domestic_violence) AS caseload_domestic_violence,
        SUM(caseload_sex_offense) AS caseload_sex_offense,
        SUM(caseload_drug) AS caseload_drug,
        SUM(caseload_mental_health) AS caseload_mental_health,
        SUM(caseload_other_case_type) AS caseload_other_case_type,
        SAFE_DIVIDE(SUM(avg_lsir_score * caseload_all), SUM(caseload_all))
            AS avg_lsir_score,
        SUM(caseload_no_lsir_score) AS caseload_no_lsir_score,
        SUM(caseload_low_risk_level) AS caseload_low_risk_level,
        SUM(caseload_high_risk_level) AS caseload_high_risk_level,
        SUM(caseload_unknown_risk_level) AS caseload_unknown_risk_level,
        SAFE_DIVIDE(SUM(avg_age * caseload_all), SUM(caseload_all)) AS avg_age,
        SUM(successful_completions) AS successful_completions,
        SUM(earned_discharge_requests) AS earned_discharge_requests,
        SUM(supervision_downgrades) AS supervision_downgrades,
        SUM(supervision_upgrades) AS supervision_upgrades,
        SUM(violations_absconded) AS violations_absconded,
        SUM(violations_legal) AS violations_legal,
        SUM(violations_technical) AS violations_technical,
        SUM(incarcerations_temporary) AS incarcerations_temporary,
        SUM(incarcerations_all) AS incarcerations_all,
        SUM(new_clients_assigned) AS new_clients_assigned,
        SUM(days_incarcerated_1yr) AS days_incarcerated_1yr,
        SUM(days_since_assignment_1yr) AS days_since_assignment_1yr,
    FROM
        `{{project_id}}.{{analyst_dataset}}.supervision_officer_office_metrics_materialized`
    GROUP BY 1, 2, 3{", 4" if level == "office" else ""}
)

# {level}-period
SELECT
    # index
    state_code,
    {index_cols},
    period,
    start_date,
    end_date,
    
    # officer attributes{officer_attributes}
    
    # caseload attributes, averaged across days
    AVG(caseload_all) AS avg_daily_caseload,
    AVG(caseload_out_of_state) AS avg_caseload_out_of_state,
    AVG(caseload_parole) AS avg_caseload_parole,
    AVG(caseload_probation) AS avg_caseload_probation,
    AVG(caseload_other_supervision_type) AS avg_caseload_other_supervision_type,
    AVG(caseload_female) AS avg_caseload_female,
    AVG(caseload_nonwhite) AS avg_caseload_nonwhite,
    AVG(caseload_general) AS avg_caseload_general,
    AVG(caseload_domestic_violence) AS avg_caseload_domestic_violence,
    AVG(caseload_sex_offense) AS avg_caseload_sex_offense,
    AVG(caseload_drug) AS avg_caseload_drug,
    AVG(caseload_mental_health) AS avg_caseload_mental_health,
    AVG(caseload_other_case_type) AS avg_caseload_other_case_type,
    AVG(avg_lsir_score) AS avg_lsir_score,
    AVG(caseload_no_lsir_score) AS avg_caseload_no_lsir_score,
    AVG(caseload_low_risk_level) AS avg_caseload_low_risk_level,
    AVG(caseload_high_risk_level) AS avg_caseload_high_risk_level,
    AVG(caseload_unknown_risk_level) AS avg_caseload_unknown_risk_level,
    AVG(avg_age) AS avg_age,
    
    # caseload events/statuses, summed across days
    SUM(successful_completions) AS successful_completions,
    SUM(earned_discharge_requests) AS earned_discharge_requests,
    SUM(supervision_downgrades) AS supervision_downgrades,
    SUM(supervision_upgrades) AS supervision_upgrades,
    SUM(violations_absconded) AS violations_absconded,
    SUM(violations_legal) AS violations_legal,
    SUM(violations_technical) AS violations_technical,
    SUM(incarcerations_temporary) AS incarcerations_temporary,
    SUM(incarcerations_all) AS incarcerations_all,
    SUM(new_clients_assigned) AS new_clients_assigned,
    SUM(days_incarcerated_1yr) AS days_incarcerated_1yr,
    SUM(days_since_assignment_1yr) AS days_since_assignment_1yr,
FROM 
    {level}_level_metrics a
INNER JOIN
    truncated_dates b
ON
    a.date BETWEEN b.start_date AND b.end_date
LEFT JOIN
    primary_offices
USING
    (state_code, {index_cols}, period, start_date, end_date)
GROUP BY 1, 2, 3, 4, 5{", 6" if level == "office" else ""}
ORDER BY 1, 2, 3, 4{", 5" if level == "office" else ""}
"""
    return view_id, view_description, query_template


# init object to hold view builders
SUPERVISION_AGGREGATED_METRICS_VIEW_BUILDERS: List[SimpleBigQueryViewBuilder] = []

# iteratively add each builder to list
for lev in ["officer", "office", "district"]:
    name, description, template = get_view_strings_by_level(lev)

    clustering_fields = ["state_code"]
    if lev == "officer":
        clustering_fields.append("supervising_officer_external_id")
    else:
        clustering_fields.append(lev)

    SUPERVISION_AGGREGATED_METRICS_VIEW_BUILDERS.append(
        SimpleBigQueryViewBuilder(
            dataset_id=ANALYST_VIEWS_DATASET,
            view_id=name,
            view_query_template=template,
            description=description,
            analyst_dataset=ANALYST_VIEWS_DATASET,
            clustering_fields=clustering_fields,
            should_materialize=True,
        )
    )

if __name__ == "__main__":
    with local_project_id_override(GCP_PROJECT_STAGING):
        for view_builder in SUPERVISION_AGGREGATED_METRICS_VIEW_BUILDERS:
            view_builder.build_and_print()