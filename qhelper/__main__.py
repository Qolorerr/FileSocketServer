import logging
from dataclasses import dataclass
from functools import wraps
from logging.config import dictConfig
from typing import Optional
from quart import Quart, jsonify, request, make_response, Response
from quart_schema import QuartSchema, validate_request, RequestSchemaValidationError

from qhelper.config import LOGGER_CONFIG, DB_PATH
from qhelper.db_session import create_session, global_init
from qhelper.encryption import encryption, decryption, init_encryption
from qhelper.devices import Device
from qhelper.users import User

app = Quart(__name__)
app.config['SECRET_KEY'] = 'af1f2ed264b7a6b18b84971091cbaceea33697bf3b80ad5cd495898c8ced0a2d09b1e8012a0' \
                           'b00868f5d6b6500a2cee7e591fbc2dd88f3f9a4caa2239d4576ac'

QuartSchema(app)

dictConfig(LOGGER_CONFIG)
logger = logging.getLogger("app")

init_encryption()

global_init(DB_PATH)

# @app.errorhandler(500)
# def error_handling_500(error):
#     return {"Error": str(error)}, 500


@app.errorhandler(RequestSchemaValidationError)
async def handle_request_validation_error(error):
    return Response("", status=400, headers={"message": error.validation_error.json()})


@dataclass
class SignUpIn:
    login: str
    email: str
    password: str


@app.post('/signup')
@validate_request(SignUpIn)
async def signup(data: SignUpIn):
    session = create_session()
    user = session.query(User).filter(User.login == data.login).first()
    if user is not None:
        return await make_response(jsonify({"message": "Login already exists"}), 401)
    user = session.query(User).filter(User.email == data.email).first()
    if user is not None:
        return await make_response(jsonify({"message": "Email already exists"}), 401)
    user = User()
    user.login = data.login
    user.email = data.email
    user.hashed_password = user.hash(data.password)
    session.add(user)
    session.commit()
    logger.info(f"New user, user_id: {user.id}")
    return Response("", status=201)


@dataclass
class PostToken:
    login_or_email: str
    password: str
    name: str
    type: str


@app.get('/get_token')
@validate_request(PostToken)
async def get_token(data: PostToken):
    session = create_session()
    user = session.query(User).filter((User.login == data.login_or_email) | (User.email == data.login_or_email)).first()
    if user is None:
        return await make_response(jsonify({"message": "Couldn't find such pair of login-password"}), 401)
    if not user.check_password(data.password):
        return await make_response(jsonify({"message": "Couldn't find such pair of login-password"}), 401)
    if data.name == "":
        return await make_response(jsonify({"message": "Device name can't be empty"}), 400)
    if data.type not in ["pc", "smartphone"]:
        return await make_response(jsonify({"message": "Device type can be only 'pc' or 'smartphone'"}), 400)
    logger.debug(f"Success login, user_id: {user.id}")
    device = session.query(Device).filter((Device.user_id == user.id) &
                                          (Device.type == data.type) &
                                          (Device.name == data.name)).first()
    if device is not None:
        return await make_response(jsonify({"token": _create_token(device)}), 201)
    device = Device()
    device.name = data.name
    device.type = data.type
    device.user_id = user.id
    session.add(device)
    session.commit()
    logger.info(f"New device, device: {device.type}{device.id}")
    return await make_response(jsonify({"token": _create_token(device)}), 201)


def _create_token(device: Device) -> str:
    return encryption(f"{device.id} {device.user_id}")


def _get_device_by_token(token: str) -> Optional[Device]:
    try:
        device_id, user_id = map(int, decryption(token).split())
    except:
        return None
    session = create_session()
    return session.query(Device).filter(Device.id == device_id and Device.user_id == user_id).first()


def token_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        data = await request.get_json()
        if 'token' in data:
            token = data['token']
        else:
            return await make_response(jsonify({"message": "Token is missing"}), 401)
        device = _get_device_by_token(token)
        if device is None:
            return Response("", status=401, headers={"message": "Invalid token"})
        return await func(device, *args, **kwargs)
    return wrapper


@dataclass
class SetNgrokIp:
    token: str
    ngrok_ip: Optional[str] = ""


@app.post('/set_ngrok_ip')
@token_required
@validate_request(SetNgrokIp)
async def set_ngrok_ip(device: Device, data: SetNgrokIp):
    session = create_session()
    session.query(Device).filter(Device.id == device.id).update({"ngrok_ip": data.ngrok_ip})
    session.commit()
    logger.debug(f"Set ngrok ip, device: {device.type}{device.id}")
    return Response("", status=200)


@dataclass
class GetNgrokIp:
    device_id: int
    token: str


@app.get('/get_ngrok_ip')
@token_required
@validate_request(GetNgrokIp)
async def get_ngrok_ip(device: Device, data: GetNgrokIp):
    session = create_session()
    device = session.query(Device).filter(Device.user_id == device.user_id,
                                          Device.id == data.device_id,
                                          Device.type == "pc").first()
    if device is None:
        return Response("Not found this device or it is offline", status=404)
    logger.debug(f"Sent ngrok ip, device: {device.type}{device.id}")
    return await make_response(jsonify({"ngrok_ip": device.ngrok_ip}), 200)


@app.get('/show_available_pc')
@token_required
async def show_available_pc(device: Device):
    return Response("Show_available_pc not working anymore. Update client", status=503)


@app.websocket('/connect')
async def connect(device: Device, device_id: str, is_managed: bool):
    return Response("Websocket not working anymore. Update client", status=503)


if __name__ == '__main__':
    try:
        app.run(port=5000, host='127.0.0.1')
    except KeyboardInterrupt:
        logger.warning(f"Disabling server")
