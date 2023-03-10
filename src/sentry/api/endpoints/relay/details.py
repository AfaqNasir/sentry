from rest_framework.request import Request
from rest_framework.response import Response

from sentry.api.base import Endpoint, pending_silo_endpoint
from sentry.api.exceptions import ResourceDoesNotExist
from sentry.api.permissions import SuperuserPermission
from sentry.models import Relay


@pending_silo_endpoint
class RelayDetailsEndpoint(Endpoint):
    private = True
    permission_classes = (SuperuserPermission,)

    def delete(self, request: Request, relay_id) -> Response:
        """
        Delete one Relay
        ````````````````
        :auth: required
        """
        try:
            relay = Relay.objects.get(id=relay_id)
        except Relay.DoesNotExist:
            raise ResourceDoesNotExist

        # TODO(hazat): Create audit entry?

        relay.delete()

        return Response(status=204)
