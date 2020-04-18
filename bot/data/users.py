import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import Column
from sqlalchemy_serializer import SerializerMixin


class User(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'users'

    id = Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = Column(sqlalchemy.String)
    lastname = Column(sqlalchemy.String)
    chat_id = Column(sqlalchemy.String)
    mainid = Column(sqlalchemy.Integer)
