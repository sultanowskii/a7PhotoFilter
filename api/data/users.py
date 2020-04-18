import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm, Column
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime


association_table = sqlalchemy.Table('users-rooms', SqlAlchemyBase.metadata,
    sqlalchemy.Column('user', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('users.id')),
    sqlalchemy.Column('room', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('rooms.id')))


class User(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'users'

    id = Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = Column(sqlalchemy.String)
    lastname = Column(sqlalchemy.String)
    # Здесь мы соединяем rooms и users с помощью вспомогательной таблицы
    rooms = orm.relation('Room',
                              secondary=association_table,
                              backref='users')
