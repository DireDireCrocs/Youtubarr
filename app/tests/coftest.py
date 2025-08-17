import os
import pytest
from django.conf import settings
from django.test import Client

@pytest.fixture(autouse=True, scope="session")
def _eager_tasks():
    os.environ["CELERY_TASK_ALWAYS_EAGER"] = "1"

@pytest.fixture(autouse=True)
def _db_tmpdir(settings, tmp_path, django_db_setup, django_db_blocker):
    # isolate sqlite DB per test run
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    settings.DATABASES["default"]["NAME"] = str(data_dir / "db.sqlite3")
    settings.STATIC_ROOT = str(tmp_path / "static")
    yield

@pytest.fixture
def client():
    return Client()
