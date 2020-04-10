import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm, Column
from sqlalchemy_serializer import SerializerMixin


class Image(SqlAlchemyBase):
    __tablename__ = 'images'

    id = Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    room_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("rooms.id"))
    room = orm.relation('Room') #   связь с Room многие к одному
