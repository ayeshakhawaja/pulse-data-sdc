## public_dashboard_views.sentence_type_by_district_by_demographics
Current incarcerated and supervised population, broken down by sentence type (probation/incarceration),
        judicial district, and demographics.

#### View schema in Big Query
This view may not be deployed to all environments yet.<br/>
[**Staging**](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-staging&page=table&project=recidiviz-staging&d=public_dashboard_views&t=sentence_type_by_district_by_demographics)
<br/>
[**Production**](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-123&page=table&project=recidiviz-123&d=public_dashboard_views&t=sentence_type_by_district_by_demographics)
<br/>

#### Dependency Trees

##### Parentage
[public_dashboard_views.sentence_type_by_district_by_demographics](../public_dashboard_views/sentence_type_by_district_by_demographics.md) <br/>
|--[shared_metric_views.single_day_supervision_population_for_spotlight](../shared_metric_views/single_day_supervision_population_for_spotlight.md) <br/>
|----[dataflow_metrics_materialized.most_recent_single_day_supervision_population_metrics](../dataflow_metrics_materialized/most_recent_single_day_supervision_population_metrics.md) <br/>
|------[dataflow_metrics_materialized.most_recent_supervision_population_metrics](../dataflow_metrics_materialized/most_recent_supervision_population_metrics.md) <br/>
|--------[dataflow_metrics.supervision_population_metrics](../../metrics/supervision/supervision_population_metrics.md) <br/>
|--[shared_metric_views.single_day_incarceration_population_for_spotlight](../shared_metric_views/single_day_incarceration_population_for_spotlight.md) <br/>
|----[dataflow_metrics_materialized.most_recent_single_day_incarceration_population_metrics_included_in_state_population](../dataflow_metrics_materialized/most_recent_single_day_incarceration_population_metrics_included_in_state_population.md) <br/>
|------[dataflow_metrics_materialized.most_recent_incarceration_population_metrics_included_in_state_population](../dataflow_metrics_materialized/most_recent_incarceration_population_metrics_included_in_state_population.md) <br/>
|--------[dataflow_metrics.incarceration_population_metrics](../../metrics/incarceration/incarceration_population_metrics.md) <br/>


##### Descendants
[public_dashboard_views.sentence_type_by_district_by_demographics](../public_dashboard_views/sentence_type_by_district_by_demographics.md) <br/>
|--[public_dashboard_views.racial_disparities](../public_dashboard_views/racial_disparities.md) <br/>
|--[validation_views.sentence_type_by_district_by_demographics_internal_consistency](../validation_views/sentence_type_by_district_by_demographics_internal_consistency.md) <br/>
|--[validation_views.sentence_type_by_district_by_demographics_internal_consistency_errors](../validation_views/sentence_type_by_district_by_demographics_internal_consistency_errors.md) <br/>
