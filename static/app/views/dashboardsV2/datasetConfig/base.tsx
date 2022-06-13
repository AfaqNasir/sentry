import {Client} from 'sentry/api';
import {OrganizationSummary, PageFilters} from 'sentry/types';
import {Series} from 'sentry/types/echarts';
import {TableData} from 'sentry/utils/discover/discoverQuery';
import {MetaType} from 'sentry/utils/discover/eventView';
import {getFieldRenderer} from 'sentry/utils/discover/fieldRenderers';

import {Widget, WidgetQuery, WidgetType} from '../types';

import {ErrorsAndTransactionsConfig} from './errorsAndTransactions';
import {IssuesConfig} from './issues';
import {ReleasesConfig} from './releases';

export type ContextualProps = {
  api?: Client;
  organization?: OrganizationSummary;
  pageFilters?: PageFilters;
};

export interface DatasetConfig<SeriesResponse, TableResponse> {
  /**
   * Transforms table API results into format that is used by
   * table and big number components
   */
  transformTable: (
    data: TableResponse,
    widgetQuery: WidgetQuery,
    contextualProps?: ContextualProps
  ) => TableData;
  /**
   * Used for mapping column names to more desirable
   * values in tables.
   */
  fieldHeaderMap?: Record<string, string>;
  /**
   * Used to select custom renderers for field types.
   */
  getCustomFieldRenderer?: (
    field: string,
    meta: MetaType,
    contextualProps?: ContextualProps
  ) => ReturnType<typeof getFieldRenderer> | null;
  /**
   * TODO: Promote to required when other configs implement this
   */
  getTableRequests?: (
    widget: Widget,
    contextualProps: ContextualProps,
    limit?: number,
    cursor?: string
  ) => ReturnType<Client['requestPromise']>[];
  /**
   * TODO: Add Description
   */
  getTimeseriesRequests?: (
    widget: Widget,
    contextualProps: ContextualProps
  ) => ReturnType<Client['requestPromise']>[];
  /**
   * Transforms timeseries API results into series data that is
   * ingestable by echarts for timeseries visualizations.
   */
  transformSeries?: (data: SeriesResponse) => Series[];
}

export function getDatasetConfig<T extends WidgetType | undefined>(
  widgetType: T
): T extends WidgetType.ISSUE
  ? typeof IssuesConfig
  : T extends WidgetType.RELEASE
  ? typeof ReleasesConfig
  : typeof ErrorsAndTransactionsConfig;

export function getDatasetConfig(
  widgetType?: WidgetType
): typeof IssuesConfig | typeof ReleasesConfig | typeof ErrorsAndTransactionsConfig {
  switch (widgetType) {
    case WidgetType.ISSUE:
      return IssuesConfig;
    case WidgetType.RELEASE:
      return ReleasesConfig;
    case WidgetType.DISCOVER:
    default:
      return ErrorsAndTransactionsConfig;
  }
}
