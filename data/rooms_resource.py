from . import db_session
from .rooms import Room
from flask import jsonify
from flask_restful import Resource
from . import rooms_parser
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