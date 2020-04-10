import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm, Column
from sqlalchemy_serializer import SerializerMixin


class Image(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'images'

    id = Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    room_id = Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("rooms.id"), default=0)  # у тех картинок, у которых нету
    # их комнаты, присваиваются 0 комнате - служебной

    # после загрузки картинки юзером для обработки, мы сразу создаем ему Image
    room = orm.relation('Room')  # связь с Room многие к одному
    name = Column(sqlalchemy.String)
