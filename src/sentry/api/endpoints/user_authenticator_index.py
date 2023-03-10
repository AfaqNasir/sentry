from rest_framework.request import Request
from rest_framework.response import Response

from sentry.api.base import control_silo_endpoint
from sentry.api.bases.user import UserEndpoint
from sentry.api.serializers import serialize
from sentry.models import Authenticator


@control_silo_endpoint
class UserAuthenticatorIndexEndpoint(UserEndpoint):
    private = True

    def get(self, request: Request, user) -> Response:
        """Returns all interface for a user (un-enrolled ones), otherwise an empty array"""

        interfaces = Authenticator.objects.all_interfaces_for_user(user, return_missing=True)
        return Response(serialize(list(interfaces)))
