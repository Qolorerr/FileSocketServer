import logging
import time
import pytest

from filesocket_server import app
from filesocket_server.encryption import decryption

LOGIN = "Tester"
EMAIL = "tester@test.com"
PASSWORD = "SecretPassword"
DEVICE_NAME = "TesterPC"
DEVICE_TYPE = "pc"
DECODED_TOKEN = "1 1"
TOKEN = "gAAAAABi88YV3akcyfpk33sy8RyNR87dnnZ1-8XFjKQ260eTQZ9KnRItVPJvsIKc8tzTKtb25JHc7G1INSEMSzTCS6zPZouHHg=="
NGROK_IP = "test ngrok ip"

logger = logging.getLogger('testing')


@pytest.fixture(autouse=True)
def slow_down_tests():
    yield
    time.sleep(3)


@pytest.mark.parametrize(
    "path, json, status",
    [
        ("/filesocket/signup", {"login": LOGIN, "email": EMAIL, "password": PASSWORD}, 201),
    ],
)
async def test_signup(path: str, json: dict, status: int) -> None:
    test_client = app.test_client()
    response = await test_client.post(path, json=json)
    if 'message' in response.headers:
        print(f"Message: {response.headers['message']}\n")
    assert response.status_code == status


@pytest.mark.parametrize(
    "path, json, status",
    [
        ("/filesocket/get_token", {"login_or_email": LOGIN, "password": PASSWORD,
                                   "name": DEVICE_NAME, "type": DEVICE_TYPE}, 201),
    ],
)
async def test_get_token(path: str, json: dict, status: int) -> None:
    test_client = app.test_client()
    response = await test_client.get(path, json=json)
    json = await response.get_json()
    if 'message' in json:
        print(f"Message: {json['message']}\n")
    assert response.status_code == status
    assert decryption(json['token']) == DECODED_TOKEN


@pytest.mark.parametrize(
    "path, json, status",
    [
        ("/filesocket/set_ngrok_ip", {"token": TOKEN, "ngrok_ip": NGROK_IP}, 200),
    ],
)
async def test_set_ngrok_ip(path: str, json: dict, status: int) -> None:
    test_client = app.test_client()
    response = await test_client.post(path, json=json)
    if 'message' in response.headers:
        print(f"Message: {response.headers['message']}\n")
    assert response.status_code == status


@pytest.mark.parametrize(
    "path, json, status",
    [
        ("/filesocket/get_ngrok_ip", {"token": TOKEN, "device_id": "1"}, 200),
    ],
)
async def test_get_ngrok_ip(path: str, json: dict, status: int) -> None:
    test_client = app.test_client()
    response = await test_client.get(path, json=json)
    if 'message' in response.headers:
        print(f"Message: {response.headers['message']}\n")
    json = await response.get_json()
    assert response.status_code == status
    assert json['ngrok_ip'] == NGROK_IP
