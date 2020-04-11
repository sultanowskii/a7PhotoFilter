from . import db_session
from .users import User
from flask import jsonify
from flask_restful import Resource
from . import users_parser
from werkzeug import exceptions

parser = users_parser.parser


class UsersResource(Resource):
    def get(self, user_id):
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        if not user:
            raise exceptions.NotFound
        return jsonify({'ser': user.to_dict()})

    def delete(self, user_id):
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        if not user:
            raise exceptions.NotFound
        session.delete(user)
        session.commit()
        return jsonify({'success': 'OK'})


class UsersListResource(Resource):
    def get(self):
        session = db_session.create_session()
        users = session.query(User).all()
        return jsonify({'users': [item.to_dict() for item in users]})

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()
        user = User(
            name=args.get('name')
        )
        session.add(user)
        session.commit()
        return jsonify({'success': 'OK'})