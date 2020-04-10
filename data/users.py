import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm, Column
from sqlalchemy_serializer import SerializerMixin


class User(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'users'

    id = Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    rooms_count = Column(sqlalchemy.Integer) #  кол-во комнат у юзера (для ограничителей)
    #   здесь должна быть связь многие-ко-многим с rooms
