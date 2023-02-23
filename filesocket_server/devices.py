import sqlalchemy
from sqlalchemy_serializer import SerializerMixin
from db_session import SqlAlchemyBase


class Device(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'devices'
    __table_args__ = {'extend_existing': True}
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    type = sqlalchemy.Column(sqlalchemy.String)
    user_id = sqlalchemy.Column(sqlalchemy.Integer)
    ngrok_ip = sqlalchemy.Column(sqlalchemy.String)
