import time
import requests
import pytest

# from qhelper import app
from qhelper.encryption import decryption, init_encryption

LOGIN = "Tester"
EMAIL = "tester@test.com"
PASSWORD = "SecretPassword"
DEVICE_NAME = "TesterPC"
DEVICE_TYPE = "pc"
DECODED_TOKEN = "1 1"
TOKEN = "gAAAAABi88YV3akcyfpk33sy8RyNR87dnnZ1-8XFjKQ260eTQZ9KnRItVPJvsIKc8tzTKtb25JHc7G1INSEMSzTCS6zPZouHHg=="


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
    # test_client = app.test_client()
    # response = await test_client.post(path, json=json)
    response = requests.post(f'http://127.0.0.1:5000{path}', json=json)
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
    response = requests.get(f'http://127.0.0.1:5000{path}', json=json)
    init_encryption()
    if 'message' in response.headers:
        print(f"Message: {response.headers['message']}\n")
    assert response.status_code == status
    assert decryption(response.headers['token']) == DECODED_TOKEN


@pytest.mark.parametrize(
    "path, json, status",
    [
        ("/change_active_mode", {"token": TOKEN, "is_active": True}, 200),
    ],
)
async def test_change_active_mode(path: str, json: dict, status: int) -> None:
    response = requests.post(f'http://127.0.0.1:5000{path}', json=json)
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
    response = requests.get(f'http://127.0.0.1:5000{path}', json=json)
    json = response.json()
    if 'message' in response.headers:
        print(f"Message: {response.headers['message']}\n")
    assert response.status_code == status
    assert json['devices'][0]["id"] == "1"
    assert json['devices'][0]["name"] == DEVICE_NAME
