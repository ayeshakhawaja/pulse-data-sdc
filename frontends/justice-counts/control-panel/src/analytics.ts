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

import { UpdatedMetricsValues } from "./shared/types";

const TEST_SENDING_ANALYTICS = false; // used for testing sending analytics in development

export const identify = (
  userId: string,
  metadata?: Record<string, unknown>
): void => {
  const fullMetadata = metadata || {};
  if (
    (process.env.NODE_ENV !== "development" &&
      process.env.NODE_ENV !== "test") ||
    TEST_SENDING_ANALYTICS
  ) {
    window.analytics.identify(userId, fullMetadata);
  } else {
    // eslint-disable-next-line
    console.log(
      `[Analytics] Identifying user id: ${userId}, with metadata: ${JSON.stringify(
        fullMetadata
      )}`
    );
  }
};

const track = (eventName: string, metadata?: Record<string, unknown>): void => {
  const fullMetadata = metadata || {};
  if (
    (process.env.NODE_ENV !== "development" &&
      process.env.NODE_ENV !== "test") ||
    TEST_SENDING_ANALYTICS
  ) {
    window.analytics.track(eventName, fullMetadata);
  } else {
    // eslint-disable-next-line
    console.log(
      `[Analytics] Tracking event name: ${eventName}, with metadata: ${JSON.stringify(
        fullMetadata
      )}`
    );
  }
};

export const trackReportCreated = (reportId: number): void => {
  track("frontend_report_created", {
    reportId,
  });
};

export const trackReportNotStartedToDraft = (reportId: number): void => {
  track("frontend_report_not_started_to_draft", {
    reportId,
  });
};

export const trackReportPublished = (
  reportId: number,
  metrics: UpdatedMetricsValues[]
): void => {
  const metricsReported = metrics.reduce((res: string[], metric) => {
    if (metric.value !== null) {
      res.push(metric.key);
    }
    return res;
  }, []);
  const metricsReportedCount = metricsReported.length;
  const metricsReportedWithContext = metrics.reduce((res: string[], metric) => {
    if (
      metric.contexts.find(
        (context) => context.value !== null && context.value !== undefined
      )
    ) {
      res.push(metric.key);
    }
    return res;
  }, []);
  const metricsReportedWithContextCount = metricsReportedWithContext.length;
  const metricsReportedWithDisaggregations = metrics.reduce(
    (res: string[], metric) => {
      if (
        metric.disaggregations.find((disaggregation) =>
          disaggregation.dimensions.find(
            (dimension) =>
              dimension.value !== undefined && dimension.value !== null
          )
        )
      ) {
        res.push(metric.key);
      }
      return res;
    },
    []
  );
  const metricsReportedWithDisaggregationsCount =
    metricsReportedWithDisaggregations.length;
  const totalMetricsCount = metrics.length;
  track("frontend_report_published", {
    reportId,
    metricsReportedCount,
    metricsReportedWithContextCount,
    metricsReportedWithDisaggregationsCount,
    totalMetricsCount,
  });
};

export const trackNetworkError = (
  path: string,
  method: string,
  status: number,
  errorMsg: string
): void => {
  track("frontend_network_error", {
    path,
    method,
    status,
    errorMsg,
  });
};

export const trackAutosaveTriggered = (reportId: number): void => {
  track("frontend_report_autosave_triggered", {
    reportId,
  });
};

export const trackAutosaveFailed = (reportId: number): void => {
  track("frontend_report_autosave_failed", {
    reportId,
  });
};

export const trackNavigation = (screen: string): void => {
  track("frontend_navigate", {
    screen,
  });
};