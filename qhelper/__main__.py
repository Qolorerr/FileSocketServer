import asyncio
from dataclasses import dataclass
from functools import wraps
from quart import Quart, jsonify, request, make_response
from quart_schema import QuartSchema, validate_request

from db_session import create_session, global_init
from encryption import encryption, decryption, init_encryption
from devices import Device
from users import User

app = Quart(__name__)
app.config['SECRET_KEY'] = 'af1f2ed264b7a6b18b84971091cbaceea33697bf3b80ad5cd495898c8ced0a2d09b1e8012a0' \
                           'b00868f5d6b6500a2cee7e591fbc2dd88f3f9a4caa2239d4576ac'

QuartSchema(app)

init_encryption()


@app.errorhandler(500)
def error_handling_500(error):
    return {"Error": str(error)}, 500


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
        return make_response(jsonify({"message": "Login already exists"}), 401)
    user = session.query(User).filter(User.email == data.email).first()
    if user is not None:
        return make_response(jsonify({"message": "Email already exists"}), 401)
    user = User()
    user.login = data.login
    user.email = data.email
    user.hashed_password = user.hash(data.password)
    session.add(user)
    session.commit()
    return make_response(201)


@dataclass
class GetTokenIn:
    login_or_email: str
    password: str
    name: str
    type: str


@app.post('/get_token')
@validate_request(GetTokenIn)
async def get_token(data: GetTokenIn):
    session = create_session()
    user = session.query(User).filter(User.login == data.login_or_email or User.email == data.login_or_email).first()
    if user is None:
        return make_response(jsonify({"message": "Couldn't find such pair of login-password"}), 401)
    if user.check_password(data.password):
        return make_response(jsonify({"message": "Couldn't find such pair of login-password"}), 401)
    if data.name == "":
        return make_response(jsonify({"message": "Device name can't be empty"}), 400)
    if data.type not in ["pc", "smartphone"]:
        return make_response(jsonify({"message": "Device type can be only 'pc' or 'smartphone'"}), 400)
    device = Device()
    device.name = data.name
    device.type = data.type
    device.user_id = user.id
    session.add(device)
    session.commit()
    return make_response(jsonify({"token": create_token(device)}), 201)


def create_token(device: Device) -> str:
    return str(encryption(f"{device.id} {device.user_id}"))


def token_required(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        token = None
        if 'token' in request.headers:
            token = request.headers['token']
        if not token:
            return make_response(jsonify({"message": "Token is missing"}), 401)
        try:
            device_id, user_id = map(int, decryption(token).split())
        except:
            return make_response(jsonify({"message": "Invalid token"}), 401)
        session = create_session()
        device = session.query(Device).filter(Device.id == device_id and Device.user_id == user_id).first()
        if device is None:
            return make_response(jsonify({"message": "Invalid token"}), 401)
        return func(device, *args, **kwargs)
    return decorator


if __name__ == '__main__':
    global_init("db/user_data.sqlite")
    app.run(port=5000, host='127.0.0.1')
