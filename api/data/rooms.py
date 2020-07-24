from .db_session import SqlAlchemyBase
import sqlalchemy
from sqlalchemy import Column, orm
from sqlalchemy_serializer import SerializerMixin
from random import randint


class Room(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'rooms'

    id = Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = Column(sqlalchemy.String)  # название комнаты
    images = orm.relation('Image', back_populates='room')
    link = Column(sqlalchemy.String)

    def generate_link(self):
        word = ''
        for i in range(randint(3, 5)):
            word += chr(randint(ord('a'), ord('z')))
        self.link = f'{self.id}*{word}'
