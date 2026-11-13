import uuid

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from api.models import Site, Tag, UUIDTaggedItem


def test_project_tags_lists_project_and_unused_tags(api_client_public, project1):
    project_tag = Tag.objects.create(name="project-tag")
    unused_tag = Tag.objects.create(name="unused-tag")
    other_tag = Tag.objects.create(name="other-tag")
    project1.tags.add(project_tag)
    UUIDTaggedItem.objects.create(
        tag=other_tag,
        content_type=ContentType.objects.get_for_model(Site),
        object_id=uuid.uuid4(),
    )

    response = api_client_public.get(reverse("projecttag-list"))

    assert response.status_code == 200
    names = [tag["name"] for tag in response.json()["results"]]
    assert project_tag.name in names
    assert unused_tag.name in names
    assert other_tag.name not in names
