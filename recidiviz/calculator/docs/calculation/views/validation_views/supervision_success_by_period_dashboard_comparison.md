## validation_views.supervision_success_by_period_dashboard_comparison

Compares counts of supervision success by period between the dashboard and the public dashboard. 

#### View schema in Big Query
This view may not be deployed to all environments yet.<br/>
[**Staging**](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-staging&page=table&project=recidiviz-staging&d=validation_views&t=supervision_success_by_period_dashboard_comparison)
<br/>
[**Production**](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-123&page=table&project=recidiviz-123&d=validation_views&t=supervision_success_by_period_dashboard_comparison)
<br/>

#### Dependency Trees

##### Parentage
[validation_views.supervision_success_by_period_dashboard_comparison](../validation_views/supervision_success_by_period_dashboard_comparison.md) <br/>
|--[public_dashboard_views.supervision_success_by_period_by_demographics](../public_dashboard_views/supervision_success_by_period_by_demographics.md) <br/>
|----[dataflow_metrics_materialized.most_recent_supervision_success_metrics](../dataflow_metrics_materialized/most_recent_supervision_success_metrics.md) <br/>
|------[dataflow_metrics.supervision_success_metrics](../../metrics/supervision/supervision_success_metrics.md) <br/>
|--[dashboard_views.supervision_termination_by_type_by_period](../dashboard_views/supervision_termination_by_type_by_period.md) <br/>
|----[dataflow_metrics_materialized.most_recent_supervision_success_metrics](../dataflow_metrics_materialized/most_recent_supervision_success_metrics.md) <br/>
|------[dataflow_metrics.supervision_success_metrics](../../metrics/supervision/supervision_success_metrics.md) <br/>


##### Descendants
This view has no child dependencies.