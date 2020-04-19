from .rooms import Room
from .users import User
from . import db_session
from . import rooms_parser
import config

from flask import jsonify
from flask_restful import Resource
from werkzeug import exceptions

parser = rooms_parser.parser


class RoomsResource(Resource):
    def get(self, room_id):
        session = db_session.create_session()
        room = session.query(Room).get(room_id)
        if not room:
            raise exceptions.NotFound
        users_list = []
        image_list = []
        for user in room.users:
            users_list.append(user.id)
        for image in room.images:
            image_list.append(image.id)
        return jsonify({'Room': {'name': room.name, 'users': users_list, 'images': image_list, 'id': room_id}})

    def delete(self, room_id):
        session = db_session.create_session()
        room = session.query(Room).get(room_id)
        if not room:
            raise exceptions.NotFound
        session.delete(room)
        session.commit()
        return jsonify({'success': 'OK'})

    def put(self, room_id):
        session = db_session.create_session()
        room = session.query(Room).get(room_id)
        if not room:
            raise exceptions.NotFound
        args = parser.parse_args()
        if args.get('name'):
            room.name = args.get('name')
        for userid in args.get('users_id').split(' '):
            user = session.query(User).get(int(userid))
            if not user:
                raise exceptions.NotFound
            if args.get('remove_user') == True:
                if user in room.users:
                    room.users.remove(user)
                else:
                    raise exceptions.NotFound
            else:
                if len(room.users) < config.ROOM_USER_LIMIT:
                    if len(user.rooms) < config.USER_ROOM_LIMIT:
                        room.users.append(user)
                    else:
                        raise exceptions.Forbidden  # временно
                else:
                    raise exceptions.Forbidden  # временно
        session.commit()
        return jsonify({'success': 'OK'})


class RoomsListResource(Resource):
    def get(self):
        session = db_session.create_session()
        rooms = session.query(Room).all()
        data = {'rooms': []}
        for item in rooms:
            users_list = []
            for user in item.users:
                users_list.append(user.id)
            data['rooms'].append({'id': item.id, 'users': users_list, 'name': item.name})
        return jsonify(data)

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()
        room = Room(
            name=args.get('name')
        )
        for userid in args.get('users_id').split(' '):
            user = session.query(User).get(int(userid))
            if not user:
                raise exceptions.NotFound
            if args.get('remove_user') == True:
                if user in room.users:
                    room.users.remove(user)
                else:
                    raise exceptions.NotFound
            else:
                if len(room.users) < config.ROOM_USER_LIMIT:
                    if len(user.rooms) < config.USER_ROOM_LIMIT:
                        room.users.append(user)
                    else:
                        raise exceptions.Forbidden  # временно
                else:
                    raise exceptions.Forbidden  # временно
        session.add(room)
        session.commit()
        return jsonify({'success': 'OK'})
