from .rooms import Room
from .users import User
from . import db_session
from . import users_parser
from .. import config

from flask import jsonify
from flask_restful import Resource

from werkzeug import exceptions

parser = users_parser.parser


class UsersResource(Resource):
    def get(self, user_id):
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        if not user:
            raise exceptions.NotFound
        rooms_list = []
        for room in user.rooms:
            rooms_list.append(room.id)
        return jsonify({'User': {'name': user.name, 'rooms': rooms_list, 'id': user_id}})

    def delete(self, user_id):
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        if not user:
            raise exceptions.NotFound
        session.delete(user)
        session.commit()
        return jsonify({'success': 'OK'})

    def put(self, user_id):
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        if not user:
            raise exceptions.NotFound
        args = parser.parse_args()
        if args.get('name'):
            user.name = args.get('name')
        if args.get('lastname'):
            user.lastname = args.get('lastname')
        for roomid in args.get('users_id').split(' '):
            room = session.query(Room).get(int(roomid))
            if not room:
                raise exceptions.NotFound
            if args.get('remove_room') == True:
                if room in user.rooms:
                    user.rooms.remove(room)
                else:
                    raise exceptions.NotFound
            else:
                if len(user.rooms) < config.USER_ROOM_LIMIT:
                    if len(room.users) < config.ROOM_USER_LIMIT:
                        user.rooms.append(room)
                    else:
                        raise exceptions.Forbidden  # временно
                else:
                    raise exceptions.Forbidden  # временно
        session.commit()
        return jsonify({'success': 'OK'})


class UsersListResource(Resource):
    def get(self):
        session = db_session.create_session()
        users = session.query(User).all()
        data = {'users': []}
        for item in users:
            rooms_list = []
            for room in item.rooms:
                rooms_list.append(room.id)
            data['users'].append({'id': item.id, 'rooms': rooms_list, 'name': item.name, 'lastname': item.lastname})
        return jsonify(data)

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()
        user = User(
            name=args.get('name'),
            lastname=args.get('lastname')
        )
        for roomid in args.get('users_id').split(' '):
            room = session.query(Room).get(int(roomid))
            if not room:
                raise exceptions.NotFound
            if args.get('remove_room') == True:
                if room in user.rooms:
                    user.rooms.remove(room)
                else:
                    raise exceptions.NotFound
            else:
                if len(user.rooms) < config.USER_ROOM_LIMIT:
                    if len(room.users) < config.ROOM_USER_LIMIT:
                        user.rooms.append(room)
                    else:
                        raise exceptions.Forbidden  # временно
                else:
                    raise exceptions.Forbidden  # временно
        session.add(user)
        session.commit()
        return jsonify({'success': 'OK', 'id': user.id})
