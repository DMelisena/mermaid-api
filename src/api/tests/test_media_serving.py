import shutil
import uuid
from pathlib import Path

import pytest
from django.conf import settings as django_settings
from django.test import Client


@pytest.mark.skipif(
    django_settings.ENVIRONMENT != "local", reason="media is served by Django only in local"
)
def test_local_media_served_without_debug(settings):
    settings.DEBUG = False
    media_root = Path(settings.MEDIA_ROOT)
    created_root = not media_root.exists()
    subdir = media_root / f"test-{uuid.uuid4().hex}"
    subdir.mkdir(parents=True)
    try:
        (subdir / "image.txt").write_bytes(b"media content")

        response = Client().get(f"{settings.MEDIA_URL}{subdir.name}/image.txt")

        assert response.status_code == 200
        assert b"".join(response.streaming_content) == b"media content"
    finally:
        shutil.rmtree(media_root if created_root else subdir)
