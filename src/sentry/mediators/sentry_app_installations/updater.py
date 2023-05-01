from sentry import analytics
from sentry.constants import SentryAppInstallationStatus
from sentry.mediators import Mediator, Param
from sentry.mediators.param import if_param
from sentry.models.integrations.sentry_app_installation import SentryAppInstallation


class Updater(Mediator):
    sentry_app_installation = Param("sentry.services.hybrid_cloud.app.RpcSentryAppInstallation")
    status = Param((str,), required=False)

    def call(self):
        self._update_status()
        return self.sentry_app_installation

    @if_param("status")
    def _update_status(self):
        # convert from string to integer
        if self.status == SentryAppInstallationStatus.INSTALLED_STR:
            SentryAppInstallation.objects.filter(id=self.sentry_app_installation.id).update(
                status=SentryAppInstallationStatus.INSTALLED
            )

    def record_analytics(self):
        analytics.record(
            "sentry_app_installation.updated",
            sentry_app_installation_id=self.sentry_app_installation.id,
            sentry_app_id=self.sentry_app_installation.sentry_app.id,
            organization_id=self.sentry_app_installation.organization_id,
        )
