## shared_metric_views.supervision_case_compliance_metrics

Case compliance metrics with supervising_officer_external_id pulled directly from raw data table for US_ID.


#### View schema in Big Query
This view may not be deployed to all environments yet.<br/>
[**Staging**](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-staging&page=table&project=recidiviz-staging&d=shared_metric_views&t=supervision_case_compliance_metrics)
<br/>
[**Production**](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-123&page=table&project=recidiviz-123&d=shared_metric_views&t=supervision_case_compliance_metrics)
<br/>

#### Dependency Trees

##### Parentage
[shared_metric_views.supervision_case_compliance_metrics](../shared_metric_views/supervision_case_compliance_metrics.md) <br/>
|--state.state_supervision_period ([BQ Staging](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-staging&page=table&project=recidiviz-staging&d=state&t=state_supervision_period)) ([BQ Prod](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-123&page=table&project=recidiviz-123&d=state&t=state_supervision_period)) <br/>
|--[dataflow_metrics_materialized.most_recent_supervision_case_compliance_metrics](../dataflow_metrics_materialized/most_recent_supervision_case_compliance_metrics.md) <br/>
|----[dataflow_metrics.supervision_case_compliance_metrics](../../metrics/supervision/supervision_case_compliance_metrics.md) <br/>


##### Descendants
[shared_metric_views.supervision_case_compliance_metrics](../shared_metric_views/supervision_case_compliance_metrics.md) <br/>
|--[shared_metric_views.supervision_mismatches_by_day](../shared_metric_views/supervision_mismatches_by_day.md) <br/>
|----[vitals_report_views.supervision_downgrade_opportunities_by_po_by_day](../vitals_report_views/supervision_downgrade_opportunities_by_po_by_day.md) <br/>
|------[dashboard_views.vitals_summaries](../dashboard_views/vitals_summaries.md) <br/>
|------[dashboard_views.vitals_time_series](../dashboard_views/vitals_time_series.md) <br/>
|--[vitals_report_views.overdue_lsir_by_po_by_day](../vitals_report_views/overdue_lsir_by_po_by_day.md) <br/>
|----[dashboard_views.vitals_summaries](../dashboard_views/vitals_summaries.md) <br/>
|----[dashboard_views.vitals_time_series](../dashboard_views/vitals_time_series.md) <br/>
|--[vitals_report_views.timely_contact_by_po_by_day](../vitals_report_views/timely_contact_by_po_by_day.md) <br/>
|----[dashboard_views.vitals_summaries](../dashboard_views/vitals_summaries.md) <br/>
|----[dashboard_views.vitals_time_series](../dashboard_views/vitals_time_series.md) <br/>
