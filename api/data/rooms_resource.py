from . import rooms_parser
from . import db_session
from .aborts import abort_if_user_is_full_of_rooms, abort_if_room_is_full_of_users, abort_if_room_not_found
from .aborts import abort_if_user_not_found
from flask import jsonify
from flask_restful import Resource, abort
import logging
from .rooms import Room
from .users import User

parser = rooms_parser.parser

logging.basicConfig(
    filename='logs.log',
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    level=logging.INFO
)


class RoomsResource(Resource):
    def get(self, room_id):
        abort_if_room_not_found(room_id)
        session = db_session.create_session()
        room = session.query(Room).get(room_id)
        users_list = []
        image_list = []
        for user in room.users:
            users_list.append(user.id)
        for image in room.images:
            image_list.append(image.id)
        return jsonify({'Room': {'name': room.name, 'users': users_list, 'images': image_list, 'id': room_id,
                                 'users_count': len(room.users), 'link': room.link, 'images_count': len(room.images)}})

    def delete(self, room_id):
        abort_if_room_not_found(room_id)
        session = db_session.create_session()
        room = session.query(Room).get(room_id)
        session.delete(room)
        session.commit()
        return jsonify({'success': 'OK'})

    def put(self, room_id):
        abort_if_room_not_found(room_id)
        session = db_session.create_session()
        room = session.query(Room).get(room_id)
        args = parser.parse_args()
        if args.get('name'):
            room.name = args.get('name')
        if args.get('users_id'):
            for userid in args.get('users_id').split(' '):
                abort_if_user_not_found(int(userid))
                user = session.query(User).get(int(userid))
                if args.get('remove_user') == True:
                    if user in room.users:
                        room.users.remove(user)
                    else:
                        abort(404, error='User to remove not found')
                else:
                    abort_if_room_is_full_of_users(room.id)
                    abort_if_user_is_full_of_rooms(user.id)
                    room.users.append(user)
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
        if args.get('remove_user'):
            e = 'Invalid json-data: \'remove_user\' is not allowed in POST'
            logging.warning(f'Bad request for /rooms/ got. Error: {e}')
            abort(400, error=f'Bad request: {e}')
        if args.get('name') == None:
            e = 'Invalid json-data: No required argument \'name\' in json'
            logging.warning(f'Bad request for /rooms/ got. Error: {e}')
            abort(400, error=f'Bad request: {e}')
        room = Room(
            name=args.get('name')
        )
        if args.get('users_id'):
            for userid in args.get('users_id').split(' '):
                abort_if_user_not_found(int(userid))
                user = session.query(User).get(int(userid))
                abort_if_user_is_full_of_rooms(user.id)
                room.users.append(user)
        session.add(room)
        session.commit()

        room.generate_link()
        session.commit()

        return jsonify({'success': 'OK', 'id': room.id})
