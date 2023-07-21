import {Fragment} from 'react';
import styled from '@emotion/styled';

import {addErrorMessage} from 'sentry/actionCreators/indicator';
import {RequestOptions} from 'sentry/api';
import {Alert} from 'sentry/components/alert';
import {Button} from 'sentry/components/button';
import DeprecatedAsyncComponent from 'sentry/components/deprecatedAsyncComponent';
import Form from 'sentry/components/forms/form';
import JsonForm from 'sentry/components/forms/jsonForm';
import {JsonFormObject} from 'sentry/components/forms/types';
import HookOrDefault from 'sentry/components/hookOrDefault';
import Panel from 'sentry/components/panels/panel';
import PanelItem from 'sentry/components/panels/panelItem';
import {IconOpen} from 'sentry/icons';
import {t} from 'sentry/locale';
import {space} from 'sentry/styles/space';
import {Integration, IntegrationProvider, ObjectStatus} from 'sentry/types';
import {getAlertText, getIntegrationStatus} from 'sentry/utils/integrationUtil';
import {normalizeUrl} from 'sentry/utils/withDomainRequired';
import withOrganization from 'sentry/utils/withOrganization';
import BreadcrumbTitle from 'sentry/views/settings/components/settingsBreadcrumb/breadcrumbTitle';

import AbstractIntegrationDetailedView, {Tab} from './abstractIntegrationDetailedView';
import {AddIntegrationButton} from './addIntegrationButton';
import InstalledIntegration from './installedIntegration';

// Show the features tab if the org has features for the integration
const integrationFeatures = {github: ['pr-comment-bot']};

const FirstPartyIntegrationAlert = HookOrDefault({
  hookName: 'component:first-party-integration-alert',
  defaultComponent: () => null,
});

const FirstPartyIntegrationAdditionalCTA = HookOrDefault({
  hookName: 'component:first-party-integration-additional-cta',
  defaultComponent: () => null,
});

type State = {
  configurations: Integration[];
  information: {providers: IntegrationProvider[]};
};

class IntegrationDetailedView extends AbstractIntegrationDetailedView<
  AbstractIntegrationDetailedView['props'],
  State & AbstractIntegrationDetailedView['state']
> {
  tabs: Tab[] = ['overview', 'configurations', 'features'];

  getEndpoints(): ReturnType<DeprecatedAsyncComponent['getEndpoints']> {
    const {organization} = this.props;
    const {integrationSlug} = this.props.params;
    return [
      [
        'information',
        `/organizations/${organization.slug}/config/integrations/?provider_key=${integrationSlug}`,
      ],
      [
        'configurations',
        `/organizations/${organization.slug}/integrations/?provider_key=${integrationSlug}&includeConfig=0`,
      ],
    ];
  }

  get integrationType() {
    return 'first_party' as const;
  }

  get provider() {
    return this.state.information.providers[0];
  }

  get description() {
    return this.metadata.description;
  }

  get author() {
    return this.metadata.author;
  }

  get alerts() {
    const provider = this.provider;
    const metadata = this.metadata;
    // The server response for integration installations includes old icon CSS classes
    // We map those to the currently in use values to their react equivalents
    // and fallback to IconFlag just in case.
    const alerts = (metadata.aspects.alerts || []).map(item => ({
      ...item,
      showIcon: true,
    }));

    if (!provider.canAdd && metadata.aspects.externalInstall) {
      alerts.push({
        type: 'warning',
        showIcon: true,
        text: metadata.aspects.externalInstall.noticeText,
      });
    }
    return alerts;
  }

  get resourceLinks() {
    const metadata = this.metadata;
    return [
      {url: metadata.source_url, title: 'View Source'},
      {url: metadata.issue_url, title: 'Report Issue'},
    ];
  }

  get metadata() {
    return this.provider.metadata;
  }

  get isEnabled() {
    return this.state.configurations.length > 0;
  }

  get installationStatus() {
    // TODO: add transations
    const {configurations} = this.state;
    const statusList = configurations.map(getIntegrationStatus);
    // if we have conflicting statuses, we have a priority order
    if (statusList.includes('active')) {
      return 'Installed';
    }
    if (statusList.includes('disabled')) {
      return 'Disabled';
    }
    if (statusList.includes('pending_deletion')) {
      return 'Pending Deletion';
    }
    return 'Not Installed';
  }

  get integrationName() {
    return this.provider.name;
  }

  get featureData() {
    return this.metadata.features;
  }

  renderTabs() {
    // TODO: Convert to styled component
    const {organization} = this.props;
    // TODO(cathy): remove feature check
    const tabs =
      this.provider.key in integrationFeatures &&
      organization.features.filter(value =>
        integrationFeatures[this.provider.key].includes(value)
      )
        ? this.tabs
        : this.tabs.filter(tab => tab !== 'features');

    return (
      <ul className="nav nav-tabs border-bottom" style={{paddingTop: '30px'}}>
        {tabs.map(tabName => (
          <li
            key={tabName}
            className={this.state.tab === tabName ? 'active' : ''}
            onClick={() => this.onTabChange(tabName)}
          >
            <CapitalizedLink>{this.getTabDisplay(tabName)}</CapitalizedLink>
          </li>
        ))}
      </ul>
    );
  }

  onInstall = (integration: Integration) => {
    // send the user to the configure integration view for that integration
    const {organization} = this.props;
    this.props.router.push(
      normalizeUrl(
        `/settings/${organization.slug}/integrations/${integration.provider.key}/${integration.id}/`
      )
    );
  };

  onRemove = (integration: Integration) => {
    const {organization} = this.props;

    const origIntegrations = [...this.state.configurations];

    const integrations = this.state.configurations.map(i =>
      i.id === integration.id
        ? {...i, organizationIntegrationStatus: 'pending_deletion' as ObjectStatus}
        : i
    );

    this.setState({configurations: integrations});

    const options: RequestOptions = {
      method: 'DELETE',
      error: () => {
        this.setState({configurations: origIntegrations});
        addErrorMessage(t('Failed to remove Integration'));
      },
    };

    this.api.request(
      `/organizations/${organization.slug}/integrations/${integration.id}/`,
      options
    );
  };

  onDisable = (integration: Integration) => {
    let url: string;

    const [domainName, orgName] = integration.domainName.split('/');
    if (integration.accountType === 'User') {
      url = `https://${domainName}/settings/installations/`;
    } else {
      url = `https://${domainName}/organizations/${orgName}/settings/installations/`;
    }

    window.open(url, '_blank');
  };

  handleExternalInstall = () => {
    this.trackIntegrationAnalytics('integrations.installation_start');
  };

  renderAlert() {
    return (
      <FirstPartyIntegrationAlert
        integrations={this.state.configurations ?? []}
        hideCTA
      />
    );
  }

  renderAdditionalCTA() {
    return (
      <FirstPartyIntegrationAdditionalCTA
        integrations={this.state.configurations ?? []}
      />
    );
  }

  renderTopButton(disabledFromFeatures: boolean, userHasAccess: boolean) {
    const {organization} = this.props;
    const provider = this.provider;
    const {metadata} = provider;

    const size = 'sm' as const;
    const priority = 'primary' as const;

    const buttonProps = {
      style: {marginBottom: space(1)},
      size,
      priority,
      'data-test-id': 'install-button',
      disabled: disabledFromFeatures,
      organization,
    };

    if (!userHasAccess) {
      return this.renderRequestIntegrationButton();
    }

    if (provider.canAdd) {
      return (
        <AddIntegrationButton
          provider={provider}
          onAddIntegration={this.onInstall}
          analyticsParams={{
            view: 'integrations_directory_integration_detail',
            already_installed: this.installationStatus !== 'Not Installed',
          }}
          {...buttonProps}
        />
      );
    }
    if (metadata.aspects.externalInstall) {
      return (
        <Button
          icon={<IconOpen />}
          href={metadata.aspects.externalInstall.url}
          onClick={this.handleExternalInstall}
          external
          {...buttonProps}
        >
          {metadata.aspects.externalInstall.buttonText}
        </Button>
      );
    }

    // This should never happen but we can't return undefined without some refactoring.
    return <Fragment />;
  }

  renderConfigurations() {
    const {configurations} = this.state;
    const {organization} = this.props;
    const provider = this.provider;

    if (!configurations.length) {
      return this.renderEmptyConfigurations();
    }

    const alertText = getAlertText(configurations);

    return (
      <Fragment>
        {alertText && (
          <Alert type="warning" showIcon>
            {alertText}
          </Alert>
        )}
        <Panel>
          {configurations.map(integration => (
            <PanelItem key={integration.id}>
              <InstalledIntegration
                organization={organization}
                provider={provider}
                integration={integration}
                onRemove={this.onRemove}
                onDisable={this.onDisable}
                data-test-id={integration.id}
                trackIntegrationAnalytics={this.trackIntegrationAnalytics}
                requiresUpgrade={!!alertText}
              />
            </PanelItem>
          ))}
        </Panel>
      </Fragment>
    );
  }

  renderFeatures() {
    const {configurations} = this.state;
    const {organization} = this.props;
    const hasIntegration = configurations ? configurations.length > 0 : false;
    const endpoint = `/organizations/${organization.slug}/`;
    const hasOrgWrite = organization.access.includes('org:write');

    const forms: JsonFormObject[] = [
      {
        fields: [
          {
            name: 'githubPRBot',
            type: 'boolean',
            label: t('Enable Pull Request Bot'),
            visible: ({features}) => features.includes('pr-comment-bot'),
            help: t(
              'Allow Sentry to comment on pull requests about issues impacting your app.'
            ),
            disabled: !hasIntegration,
            disabledReason: t(
              'You must have a GitHub integration to enable this feature.'
            ),
          },
        ],
      },
    ];

    const initialData = {
      githubPRBot: organization.githubPRBot,
    };

    return (
      <Form
        apiMethod="PUT"
        apiEndpoint={endpoint}
        saveOnBlur
        allowUndo
        initialData={initialData}
        onSubmitError={() => addErrorMessage('Unable to save change')}
      >
        <JsonForm
          disabled={!hasOrgWrite}
          features={organization.features}
          forms={forms}
        />
      </Form>
    );
  }

  renderBody() {
    return (
      <Fragment>
        <BreadcrumbTitle routes={this.props.routes} title={this.integrationName} />
        {this.renderAlert()}
        {this.renderTopSection()}
        {this.renderTabs()}
        {this.state.tab === 'overview'
          ? this.renderInformationCard()
          : this.state.tab === 'configurations'
          ? this.renderConfigurations()
          : this.renderFeatures()}
      </Fragment>
    );
  }
}

export default withOrganization(IntegrationDetailedView);

const CapitalizedLink = styled('a')`
  text-transform: capitalize;
`;
