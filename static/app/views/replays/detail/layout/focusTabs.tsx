import {Fragment, ReactNode} from 'react';
import queryString from 'query-string';

import FeatureBadge from 'sentry/components/featureBadge';
import ListLink from 'sentry/components/links/listLink';
import ScrollableTabs from 'sentry/components/replays/scrollableTabs';
import {t} from 'sentry/locale';
import type {Organization} from 'sentry/types';
import {trackAnalytics} from 'sentry/utils/analytics';
import useActiveReplayTab, {TabKey} from 'sentry/utils/replays/hooks/useActiveReplayTab';
import {useLocation} from 'sentry/utils/useLocation';
import useOrganization from 'sentry/utils/useOrganization';

function getReplayTabs(organization: Organization): Record<TabKey, ReactNode> {
  const hasTraceTable =
    true || organization.features.includes('session-replay-trace-table');

  return {
    [TabKey.CONSOLE]: t('Console'),
    [TabKey.NETWORK]: t('Network'),
    [TabKey.DOM]: t('DOM Events'),
    [TabKey.ERRORS]: (
      <Fragment>
        {t('Errors')} <FeatureBadge type="new" />
      </Fragment>
    ),
    [TabKey.MEMORY]: t('Memory'),
    [TabKey.TRACE]: hasTraceTable ? null : t('Trace'),
    [TabKey.TRACE_TABLE]: hasTraceTable ? (
      <Fragment>
        {t('Trace')} <FeatureBadge type="new" />
      </Fragment>
    ) : null,
  };
}

type Props = {
  className?: string;
};

function FocusTabs({className}: Props) {
  const organization = useOrganization();
  const {pathname, query} = useLocation();
  const {getActiveTab, setActiveTab} = useActiveReplayTab();
  const activeTab = getActiveTab();

  return (
    <ScrollableTabs className={className} underlined>
      {Object.entries(getReplayTabs(organization)).map(([tab, label]) =>
        label ? (
          <ListLink
            key={tab}
            isActive={() => tab === activeTab}
            to={`${pathname}?${queryString.stringify({...query, t_main: tab})}`}
            onClick={e => {
              e.preventDefault();
              setActiveTab(tab);

              trackAnalytics('replay.details-tab-changed', {
                tab,
                organization,
              });
            }}
          >
            {label}
          </ListLink>
        ) : null
      )}
    </ScrollableTabs>
  );
}

export default FocusTabs;
