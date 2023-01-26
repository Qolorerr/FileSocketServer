import asyncio
import json
import logging
import time
# import requests
import pytest
from quart.testing.connections import TestWebsocketConnection, WebsocketResponseError

from qhelper import app
from qhelper.encryption import decryption

LOGIN = "Tester"
EMAIL = "tester@test.com"
PASSWORD = "SecretPassword"
DEVICE_NAME = "TesterPC"
DEVICE_TYPE = "pc"
DECODED_TOKEN = "1 1"
TOKEN = "gAAAAABi88YV3akcyfpk33sy8RyNR87dnnZ1-8XFjKQ260eTQZ9KnRItVPJvsIKc8tzTKtb25JHc7G1INSEMSzTCS6zPZouHHg=="

logger = logging.getLogger('testing')


@pytest.fixture(autouse=True)
def slow_down_tests():
    yield
    time.sleep(1)


@pytest.mark.parametrize(
    "path, json, status",
    [
        ("/signup", {"login": LOGIN, "email": EMAIL, "password": PASSWORD}, 201),
    ],
)
async def test_signup(path: str, json: dict, status: int) -> None:
    test_client = app.test_client()
    response = await test_client.post(path, json=json)
    # response = requests.post(f'http://127.0.0.1:5000{path}', json=json)
    if 'message' in response.headers:
        print(f"Message: {response.headers['message']}\n")
    assert response.status_code == status


@pytest.mark.parametrize(
    "path, json, status",
    [
        ("/get_token", {"login_or_email": LOGIN, "password": PASSWORD, "name": DEVICE_NAME, "type": DEVICE_TYPE}, 201),
    ],
)
async def test_get_token(path: str, json: dict, status: int) -> None:
    test_client = app.test_client()
    response = await test_client.get(path, json=json)
    if 'message' in response.headers:
        print(f"Message: {response.headers['message']}\n")
    json = await response.get_json()
    assert response.status_code == status
    assert decryption(json['token']) == DECODED_TOKEN


@pytest.mark.parametrize(
    "path, json, status",
    [
        ("/change_active_mode", {"token": TOKEN, "is_active": True}, 200),
    ],
)
async def test_change_active_mode(path: str, json: dict, status: int) -> None:
    test_client = app.test_client()
    response = await test_client.post(path, json=json)
    if 'message' in response.headers:
        print(f"Message: {response.headers['message']}\n")
    assert response.status_code == status


@pytest.mark.parametrize(
    "path, json, status",
    [
        ("/show_available_pc", {"token": TOKEN}, 200),
    ],
)
async def test_show_available_pc(path: str, json: dict, status: int) -> None:
    test_client = app.test_client()
    response = await test_client.get(path, json=json)
    json = await response.get_json()
    if 'message' in response.headers:
        print(f"Message: {response.headers['message']}\n")
    assert response.status_code == status
    assert json['devices'][0]["id"] == "1"
    assert json['devices'][0]["name"] == DEVICE_NAME


async def _receive(test_websocket: TestWebsocketConnection) -> str:
    return await test_websocket.receive()


# TODO: Fix this test
@pytest.mark.parametrize(
    "path, header, message",
    [
        ("/connect", {"token": TOKEN, "device_id": "1"}, {"message": "test message"}),
        ("/connect", {"token": TOKEN, "is_managed": True}, {"message": "test message"}),
    ],
)
async def test_connect(path: str, header: dict, message: dict) -> None:
    test_client = app.test_client()
    try:
        async with test_client.websocket(path, headers=header) as test_websocket:
            task = asyncio.ensure_future(_receive(test_websocket))
            logger.debug("Created receiver")
            await test_websocket.send(json.dumps(message))
            logger.debug("Sent message")
            time.sleep(1)
            result = await task
            logger.debug("Got message")
            assert json.loads(result) == message
    except WebsocketResponseError as error:
        logger.exception(f"Code: {error.response.status_code}, args: {error.args}")
