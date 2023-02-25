import hashlib
import sqlalchemy
from sqlalchemy_serializer import SerializerMixin
from filesocket_server.db_session import SqlAlchemyBase


class User(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    login = sqlalchemy.Column(sqlalchemy.String)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String)

    def check_password(self, password):
        h = hashlib.sha3_512()
        h.update(password.encode('UTF-8'))
        return self.hashed_password == h.hexdigest()

    @staticmethod
    def hash(password):
        h = hashlib.sha3_512()
        h.update(password.encode('UTF-8'))
        return h.hexdigest()
