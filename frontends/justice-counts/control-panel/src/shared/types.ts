// Recidiviz - a data platform for criminal justice reform
// Copyright (C) 2022 Recidiviz, Inc.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
// =============================================================================

export enum Permission {
  CREATE_REPORT = "create:report:all",
}

export type ReportFrequency = "MONTHLY" | "ANNUAL";

export type ReportStatus = "NOT_STARTED" | "DRAFT" | "PUBLISHED";

export interface ReportOverview {
  id: number;
  month: number;
  year: number;
  frequency: ReportFrequency;
  last_modified_at: string | null;
  editors: string[];
  status: ReportStatus;
}

export interface Report extends ReportOverview {
  metrics: Metric[];
}

export interface Metric {
  key: string;
  display_name: string;
  description: string;
  reporting_note: string;
  value: string | number | boolean | null | undefined;
  unit: string;
  category: string;
  label: string;
  definitions: MetricDefinition[];
  contexts: MetricContext[];
  disaggregations: MetricDisaggregations[];
}

export interface MetricDefinition {
  term: string;
  definition: string;
}

export interface MetricContext {
  key: string;
  display_name: string | null | undefined;
  reporting_note: string | null | undefined;
  required: boolean;
  type: string;
  value: string | number | boolean | null | undefined;
}

export interface MetricDisaggregations {
  key: string;
  display_name: string;
  dimensions: MetricDisaggregationDimensions[];
  required: boolean;
  helper_text: string | null | undefined;
}

export interface MetricDisaggregationDimensions {
  key: string;
  label: string;
  value: string | number | boolean | null | undefined;
  reporting_note: string;
}

export interface CreateReportFormValuesType extends Record<string, unknown> {
  month: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12;
  year: number;
  frequency: "MONTHLY" | "ANNUAL";
}

export type FormContexts = {
  [contextKey: string]: string | number;
};

export type FormDimensions = {
  [dimensionKey: string]: string | number;
};

export type FormDisaggregations = {
  [disaggregationKey: string]: FormDimensions;
};

export type FormMetric = {
  value: string | number;
  contexts: FormContexts;
  disaggregations: FormDisaggregations;
};

export type FormReport = {
  [metricKey: string]: FormMetric;
};