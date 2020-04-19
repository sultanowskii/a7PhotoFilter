import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import Column, orm
from sqlalchemy_serializer import SerializerMixin


class Room(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'rooms'

    id = Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = Column(sqlalchemy.String)  # название комнаты
    images = orm.relation('Image', back_populates='room')
