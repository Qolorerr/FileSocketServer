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
    assert response.status_code == status


@pytest.mark.parametrize(
    "path, json, status",
    [
        ("/get_token", {"login_or_email": LOGIN, "password": PASSWORD, "name": DEVICE_NAME, "type": DEVICE_TYPE}, 201),
    ],
)
async def test_get_token(path: str, json: dict, status: int) -> None:
    response = requests.post(f'http://127.0.0.1:5000{path}', json=json)
    init_encryption()
    assert response.status_code == status
    assert decryption(response.headers['token']) == DECODED_TOKEN
