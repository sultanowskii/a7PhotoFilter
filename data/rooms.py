import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm, Column
from sqlalchemy_serializer import SerializerMixin


class Room(SqlAlchemyBase):
    __tablename__ = 'rooms'

    id = Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = Column(sqlalchemy.String)    #  название комнаты
    # здесь нужно сделать многие-ко-многим с юзером
    photo_count = Column(sqlalchemy.Integer) #  кол-во фото в комнате (для лимитов)