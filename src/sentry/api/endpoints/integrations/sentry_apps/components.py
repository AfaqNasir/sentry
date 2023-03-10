from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from sentry.api.base import pending_silo_endpoint, region_silo_endpoint
from sentry.api.bases import (
    OrganizationEndpoint,
    SentryAppBaseEndpoint,
    add_integration_platform_metric_tag,
)
from sentry.api.paginator import OffsetPaginator
from sentry.api.serializers import serialize
from sentry.coreapi import APIError
from sentry.mediators import sentry_app_components
from sentry.models import Project, SentryAppComponent, SentryAppInstallation


# TODO(mgaeta): These endpoints are doing the same thing, but one takes a
#  project and the other takes a sentry app. It would be better to have a single
#  endpoint that can take project_id or sentry_app_id as a query parameter.
@pending_silo_endpoint
class SentryAppComponentsEndpoint(SentryAppBaseEndpoint):
    private = True

    def get(self, request: Request, sentry_app) -> Response:
        return self.paginate(
            request=request,
            queryset=sentry_app.components.all(),
            paginator_cls=OffsetPaginator,
            on_results=lambda x: serialize(x, request.user, errors=[]),
        )


@region_silo_endpoint
class OrganizationSentryAppComponentsEndpoint(OrganizationEndpoint):
    private = True

    @add_integration_platform_metric_tag
    def get(self, request: Request, organization) -> Response:
        project_id = request.GET.get("projectId")
        if not project_id:
            raise ValidationError("Required parameter 'projectId' is missing")

        try:
            project = Project.objects.get(id=project_id, organization_id=organization.id)
        except Project.DoesNotExist:
            return Response([], status=404)

        components = []
        errors = []

        for install in SentryAppInstallation.objects.get_installed_for_organization(
            organization.id
        ):
            _components = SentryAppComponent.objects.filter(sentry_app_id=install.sentry_app_id)

            if "filter" in request.GET:
                _components = _components.filter(type=request.GET["filter"])

            for component in _components:
                try:
                    sentry_app_components.Preparer.run(
                        component=component, install=install, project=project
                    )
                except APIError:
                    errors.append(str(component.uuid))

                components.append(component)

        return self.paginate(
            request=request,
            queryset=components,
            paginator_cls=OffsetPaginator,
            on_results=lambda x: serialize(x, request.user, errors=errors),
        )
