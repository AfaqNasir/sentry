from rest_framework.request import Request
from rest_framework.response import Response

from sentry.api.base import pending_silo_endpoint
from sentry.api.bases import SentryAppBaseEndpoint
from sentry.api.bases.avatar import AvatarMixin
from sentry.api.serializers.rest_framework.sentry_app import SentryAppAvatarSerializer
from sentry.models import SentryAppAvatar


@pending_silo_endpoint
class SentryAppAvatarEndpoint(AvatarMixin, SentryAppBaseEndpoint):
    private = True
    object_type = "sentry_app"
    model = SentryAppAvatar
    serializer_cls = SentryAppAvatarSerializer

    def get(self, request: Request, **kwargs) -> Response:
        return super().get(request, access=request.access, **kwargs)

    def put(self, request: Request, **kwargs) -> Response:
        return super().put(request, access=request.access, **kwargs)

    def get_avatar_filename(self, obj):
        return f"{obj.slug}.png"
