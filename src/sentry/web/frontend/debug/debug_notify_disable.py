from django.http import HttpRequest, HttpResponse
from django.views.generic import View

from sentry.models import Organization, OrganizationMember, User
from sentry.tasks.integrations.disabled_notif import IntegrationBrokenNotification

from .mail import render_preview_email_for_notification


class DebugNotifyDisableView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        org = Organization(id=1, slug="default", name="Default")
        requester = User(name="Rick Swan")
        recipient = User(name="James Bond")
        recipient_member = OrganizationMember(user_id=recipient.id, organization=org)

        notification = IntegrationBrokenNotification(
            org,
            requester,
            provider_type="first_party",
            provider_slug="slack",
            provider_name="Slack",
        )

        # hack to avoid a query
        #   notification.role_based_recipient_strategy.set_member_in_cache(recipient_member)
        return render_preview_email_for_notification(notification, recipient)
