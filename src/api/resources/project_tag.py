from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from ..models import Project, Tag
from ..permissions import UnauthenticatedReadOnlyPermission
from .base import BaseAPIFilterSet, BaseAPISerializer, BaseApiViewSet


class ProjectTagSerializer(BaseAPISerializer):
    class Meta:
        model = Tag
        exclude = []


class ProjectTagFilterSet(BaseAPIFilterSet):
    class Meta:
        model = Tag
        fields = ["name", "status"]


class ProjectTagViewSet(BaseApiViewSet):
    method_authentication_classes = {"GET": []}
    permission_classes = [UnauthenticatedReadOnlyPermission]
    filterset_class = ProjectTagFilterSet
    serializer_class = ProjectTagSerializer
    queryset = Tag.objects.none()

    def get_queryset(self):
        # Looked up per request, not at import: importing the URLconf must not
        # query the DB, or `migrate` fails on an empty database.
        pt = ContentType.objects.get_for_model(Project)
        return (
            Tag.objects.filter(
                Q(tagged_items__content_type_id=pt.pk) | Q(tagged_items__isnull=True)
            )
            .distinct()
            .order_by("name")
        )
