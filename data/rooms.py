import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import Column
from sqlalchemy_serializer import SerializerMixin


class Room(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'rooms'

    id = Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = Column(sqlalchemy.String)  # название комнаты
    photo_count = Column(sqlalchemy.Integer, default=0)  # кол-во фото в комнате (для лимитов)
