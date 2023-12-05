""" test the server endpoints """
import pytest
from vigil_server import app


@pytest.fixture()
def vigil_app():
    yield app


@pytest.fixture()
def client(vigil_app):
    return vigil_app.test_client()


@pytest.fixture()
def runner(vigil_app):
    return vigil_app.test_cli_runner()


def test_cache_clear(client):
    response = client.post("/cache/clear")
    assert b"Cache cleared" in response.data
