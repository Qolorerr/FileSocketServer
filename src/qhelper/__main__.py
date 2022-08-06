import asyncio

from quart import Quart

from src.qhelper import db_session


app = Quart(__name__)


if __name__ == '__main__':
    db_session.global_init("db/user_data.sqlite")
    app.run(port=5000, host='127.0.0.1')
