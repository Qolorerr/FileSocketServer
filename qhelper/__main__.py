import asyncio
from dataclasses import dataclass
from functools import wraps
from logging.config import dictConfig
from typing import Optional
from quart import Quart, jsonify, request, make_response, Response, websocket
from quart.logging import create_logger
from quart_schema import QuartSchema, validate_request, RequestSchemaValidationError

from qhelper.db_session import create_session, global_init
from qhelper.encryption import encryption, decryption, init_encryption
from qhelper.devices import Device
from qhelper.broker import Broker
from qhelper.users import User

app = Quart(__name__)
app.config['SECRET_KEY'] = 'af1f2ed264b7a6b18b84971091cbaceea33697bf3b80ad5cd495898c8ced0a2d09b1e8012a0' \
                           'b00868f5d6b6500a2cee7e591fbc2dd88f3f9a4caa2239d4576ac'

QuartSchema(app)

dictConfig({
    'version': 1,
    'loggers': {
        'quart.app': {
            'level': 'INFO',
        },
    },
})
logger = create_logger(app)

broker = Broker(logger)

init_encryption()

global_init("db/user_data.sqlite")

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
    device = Device()
    device.name = data.name
    device.type = data.type
    device.user_id = user.id
    session.add(device)
    session.commit()
    return Response("", status=201, headers={"token": _create_token(device)})


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
class PostActiveMode:
    is_active: bool
    token: str


@app.post('/change_active_mode')
@token_required
@validate_request(PostActiveMode)
async def change_active_mode(device: Device, data: PostActiveMode):
    session = create_session()
    session.query(Device).filter(Device.id == device.id).update({"is_active": data.is_active})
    session.commit()
    return Response("", status=200)


@app.get('/show_available_pc')
@token_required
async def show_available_pc(device: Device):
    session = create_session()
    devices = session.query(Device).filter(Device.user_id == device.user_id,
                                           Device.type == "pc",
                                           Device.is_active == 1).all()
    return await make_response(jsonify({"devices": [{"id": str(pc.id), "name": pc.name} for pc in devices]}), 200)


async def _receive(device_from: Device, device_to_id: str) -> None:
    while True:
        message = await websocket.receive()
        logger.debug("__main__._receive\tmessage: %r", message)
        await broker.publish(device_from, device_to_id, message)


def ws_validate_request(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        data = websocket.headers
        if 'token' in data and 'device_id' in data:
            token = data['token']
            device_id = data['device_id']
        else:
            return await make_response(jsonify({"message": "Token or device_id is missing"}), 401)
        device = _get_device_by_token(token)
        if device is None:
            return Response("", status=401, headers={"message": "Invalid token"})
        return await func(device, device_id, *args, **kwargs)
    return wrapper


@app.websocket('/connect')
@ws_validate_request
async def connect(device: Device, device_id: str):
    try:
        task = asyncio.ensure_future(_receive(device, device_id))
        logger.debug("__main__.connect\tCreated task")
        async for message in broker.subscribe(device):
            logger.debug("__main__.connect\tAsync for message: %r", message)
            await websocket.send(message)
    finally:
        task.cancel()
        logger.debug("__main__.connect\tTask canceled")
        await task


if __name__ == '__main__':
    app.run(port=5000, host='127.0.0.1')
