from .rooms import Room
from .users import User
from . import db_session
from . import users_parser
import config

from flask import jsonify
from flask_restful import Resource, abort
from .aborts import abort_if_user_is_full_of_rooms, abort_if_room_is_full_of_users, abort_if_room_not_found
from .aborts import abort_if_user_not_found

parser = users_parser.parser


class UsersResource(Resource):
    def get(self, user_id):
        abort_if_user_not_found(user_id)
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        rooms_list = []
        for room in user.rooms:
            rooms_list.append(room.id)
        return jsonify({'User': {'name': user.name, 'rooms': rooms_list, 'id': user_id}})

    def delete(self, user_id):
        abort_if_user_not_found(user_id)
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        session.delete(user)
        session.commit()
        return jsonify({'success': 'OK'})

    def put(self, user_id):
        abort_if_user_not_found(user_id)
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        args = parser.parse_args()
        if args.get('name'):
            user.name = args.get('name')
        if args.get('lastname'):
            user.lastname = args.get('lastname')
        if args.get('user_id'):
            for roomid in args.get('users_id').split(' '):
                abort_if_room_not_found(int(roomid))
                room = session.query(Room).get(int(roomid))
                if args.get('remove_room') == True:
                    if room in user.rooms:
                        user.rooms.remove(room)
                    else:
                        abort(404, error='Room to remove not found')
                else:
                    abort_if_user_is_full_of_rooms(user.id)
                    abort_if_room_is_full_of_users(room.id)
                    user.rooms.append(room)
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
        if args.get('user_id'):
            for roomid in args.get('users_id').split(' '):
                abort_if_room_not_found(roomid)
                room = session.query(Room).get(int(roomid))
                abort_if_room_is_full_of_users(room.id)
                user.rooms.append(room)
        session.add(user)
        session.commit()
        return jsonify({'success': 'OK', 'id': user.id})
