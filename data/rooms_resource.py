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
        return jsonify({'ser': room.to_dict()})

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
        if args.get('user_id'):
            user = session.query(User).filter(User.id == args.get('user_id')).first()
            if user:
                if args.get('remove_user') == True:
                    if user in room.users:
                        room.users.remove(user)
                    else:
                        raise exceptions.NotFound
                else:
                    if len(room.users) < config.room_user_limit:
                        if len(user.rooms) < config.user_room_limit:
                            room.users.append(user)
                        else:
                            raise exceptions.Forbidden  # временно
                    else:
                        raise exceptions.Forbidden  # временно
            else:
                raise exceptions.NotFound
        session.commit()
        return jsonify({'success': 'OK'})


class RoomsListResource(Resource):
    def get(self):
        session = db_session.create_session()
        rooms = session.query(Room).all()
        return jsonify({'rooms': [item.to_dict() for item in rooms]})

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()
        room = Room(
            name=args.get('name')
        )
        session.add(room)
        session.commit()
        return jsonify({'success': 'OK'})
