## justice_counts_jails.population_jail_fetch
POPULATION_JAIL raw data

#### View schema in Big Query
This view may not be deployed to all environments yet.<br/>
[**Staging**](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-staging&page=table&project=recidiviz-staging&d=justice_counts_jails&t=population_jail_fetch)
<br/>
[**Production**](https://console.cloud.google.com/bigquery?pli=1&p=recidiviz-123&page=table&project=recidiviz-123&d=justice_counts_jails&t=population_jail_fetch)
<br/>

#### Dependency Trees

##### Parentage
[justice_counts_jails.population_jail_fetch](../justice_counts_jails/population_jail_fetch.md) <br/>
|--[justice_counts.report_table_instance](../justice_counts/report_table_instance.md) <br/>
|--[justice_counts.report_table_definition](../justice_counts/report_table_definition.md) <br/>
|--[justice_counts.cell](../justice_counts/cell.md) <br/>


##### Descendants
[justice_counts_jails.population_jail_fetch](../justice_counts_jails/population_jail_fetch.md) <br/>
|--[justice_counts_jails.population_jail_dropped_county_countyfips_state](../justice_counts_jails/population_jail_dropped_county_countyfips_state.md) <br/>
|----[justice_counts_jails.population_jail_monthly_partitions](../justice_counts_jails/population_jail_monthly_partitions.md) <br/>
|------[justice_counts_jails.population_jail_aggregated_monthly](../justice_counts_jails/population_jail_aggregated_monthly.md) <br/>
|--------[justice_counts_jails.population_jail_with_resident](../justice_counts_jails/population_jail_with_resident.md) <br/>
|----------[justice_counts_jails.incarceration_rate_jail_dropped_state](../justice_counts_jails/incarceration_rate_jail_dropped_state.md) <br/>
|------------[justice_counts_jails.incarceration_rate_jail_with_resident](../justice_counts_jails/incarceration_rate_jail_with_resident.md) <br/>
|--------------[justice_counts_jails.incarceration_rate_jail_compared](../justice_counts_jails/incarceration_rate_jail_compared.md) <br/>
|----------------[justice_counts_jails.incarceration_rate_jail_with_dimensions](../justice_counts_jails/incarceration_rate_jail_with_dimensions.md) <br/>
|------------------[justice_counts_jails.incarceration_rate_jail_percentage_covered](../justice_counts_jails/incarceration_rate_jail_percentage_covered.md) <br/>
|--------------------[justice_counts_jails.incarceration_rate_jail_output](../justice_counts_jails/incarceration_rate_jail_output.md) <br/>
|----------------------[justice_counts_dashboard.unified_jails_metrics_monthly](../justice_counts_dashboard/unified_jails_metrics_monthly.md) <br/>
|----------------------[justice_counts_jails.percentage_covered_county](../justice_counts_jails/percentage_covered_county.md) <br/>
|------------------------[justice_counts_dashboard.unified_jails_metrics_monthly](../justice_counts_dashboard/unified_jails_metrics_monthly.md) <br/>
|----------[justice_counts_jails.population_jail_filtered_for_comparison](../justice_counts_jails/population_jail_filtered_for_comparison.md) <br/>
|------------[justice_counts_jails.population_jail_filtered_dropped_state](../justice_counts_jails/population_jail_filtered_dropped_state.md) <br/>
|--------------[justice_counts_jails.population_jail_aggregated_filtered_compare](../justice_counts_jails/population_jail_aggregated_filtered_compare.md) <br/>
|----------------[justice_counts_jails.population_jail_state_compared](../justice_counts_jails/population_jail_state_compared.md) <br/>
|------------------[justice_counts_jails.population_jail_union](../justice_counts_jails/population_jail_union.md) <br/>
|--------------------[justice_counts_jails.population_jail_with_dimensions](../justice_counts_jails/population_jail_with_dimensions.md) <br/>
|----------------------[justice_counts_jails.population_jail_percentage_covered](../justice_counts_jails/population_jail_percentage_covered.md) <br/>
|------------------------[justice_counts_jails.population_jail_output](../justice_counts_jails/population_jail_output.md) <br/>
|--------------------------[justice_counts_dashboard.unified_jails_metrics_monthly](../justice_counts_dashboard/unified_jails_metrics_monthly.md) <br/>
|--------------[justice_counts_jails.population_jail_aggregated_filtered_input](../justice_counts_jails/population_jail_aggregated_filtered_input.md) <br/>
|----------------[justice_counts_jails.population_jail_state_compared](../justice_counts_jails/population_jail_state_compared.md) <br/>
|------------------[justice_counts_jails.population_jail_union](../justice_counts_jails/population_jail_union.md) <br/>
|--------------------[justice_counts_jails.population_jail_with_dimensions](../justice_counts_jails/population_jail_with_dimensions.md) <br/>
|----------------------[justice_counts_jails.population_jail_percentage_covered](../justice_counts_jails/population_jail_percentage_covered.md) <br/>
|------------------------[justice_counts_jails.population_jail_output](../justice_counts_jails/population_jail_output.md) <br/>
|--------------------------[justice_counts_dashboard.unified_jails_metrics_monthly](../justice_counts_dashboard/unified_jails_metrics_monthly.md) <br/>
|----------[justice_counts_jails.population_jail_unfiltered_dropped_state](../justice_counts_jails/population_jail_unfiltered_dropped_state.md) <br/>
|------------[justice_counts_jails.population_jail_unfiltered_county](../justice_counts_jails/population_jail_unfiltered_county.md) <br/>
|--------------[justice_counts_jails.population_jail_county_compared](../justice_counts_jails/population_jail_county_compared.md) <br/>
|----------------[justice_counts_jails.population_jail_union](../justice_counts_jails/population_jail_union.md) <br/>
|------------------[justice_counts_jails.population_jail_with_dimensions](../justice_counts_jails/population_jail_with_dimensions.md) <br/>
|--------------------[justice_counts_jails.population_jail_percentage_covered](../justice_counts_jails/population_jail_percentage_covered.md) <br/>
|----------------------[justice_counts_jails.population_jail_output](../justice_counts_jails/population_jail_output.md) <br/>
|------------------------[justice_counts_dashboard.unified_jails_metrics_monthly](../justice_counts_dashboard/unified_jails_metrics_monthly.md) <br/>
|------------[justice_counts_jails.population_jail_unfiltered_state](../justice_counts_jails/population_jail_unfiltered_state.md) <br/>
|--------------[justice_counts_jails.population_jail_union](../justice_counts_jails/population_jail_union.md) <br/>
|----------------[justice_counts_jails.population_jail_with_dimensions](../justice_counts_jails/population_jail_with_dimensions.md) <br/>
|------------------[justice_counts_jails.population_jail_percentage_covered](../justice_counts_jails/population_jail_percentage_covered.md) <br/>
|--------------------[justice_counts_jails.population_jail_output](../justice_counts_jails/population_jail_output.md) <br/>
|----------------------[justice_counts_dashboard.unified_jails_metrics_monthly](../justice_counts_dashboard/unified_jails_metrics_monthly.md) <br/>
