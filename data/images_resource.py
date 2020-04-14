from .images import Image
from .rooms import Room
from . import db_session
from . import filters
from . import images_parser
from .. import config

from flask import jsonify, request
from flask_restful import Resource
from werkzeug import exceptions

import base64
from datetime import datetime
from io import BytesIO
from PIL import Image as PilImage

images_parser = images_parser.parser


class ImagesResource(Resource):
    def get(self, image_id):
        args = request.args
        session = db_session.create_session()
        image = session.query(Image).get(image_id)  # image должен быть файлом
        if not image:
            raise exceptions.NotFound
        if args.get('action') == 'applyfilter' and args.get('fid', None):
            image = filters.add_filter(image, request.args['fid'])
        buf = BytesIO()
        image.save(buf, format='JPEG')
        byte_im = buf.getvalue()
        string_data = base64.b64encode(byte_im).decode('utf-8')
        return jsonify({'Image': string_data})

    def delete(self, image_id):
        session = db_session.create_session()
        image = session.query(Image).get(image_id).first()
        if not image:
            raise exceptions.NotFound
        image.room.image_count -= 1
        image.room = None
        image.room_id = None
        session.delete(image)
        session.commit()
        return jsonify({'success': 'OK'})

    def put(self, image_id):
        session = db_session.create_session()
        image = session.query(Image).get(image_id).first()
        if not image:
            raise exceptions.NotFound
        args = images_parser.parse_args()
        if args.get('name'):
            image.name = args.get('name')
        if args.get('room_id'):
            room = session.query(Room).filter(Room.id == args.get('room_id')).first()
            if room:
                if args.get('remove_room') == True:
                    image.room = None
                    image.room_id = None
                    room.image_count -= 1
                else:
                    if room.image_count < config.room_image_limit:
                        image.room_id = room.id
                        image.room = room
                        room.image_count += 1
                    else:
                        raise exceptions.Forbidden  # временно
            else:
                raise exceptions.NotFound
        session.commit()
        return jsonify({'success': 'OK'})


class ImagesListResource(Resource):
    def get(self):
        session = db_session.create_session()
        images = session.query(Image).all()
        return jsonify({'Images': [item.to_dict(
            only=('id', 'image')) for item in images]})

    def post(self):
        args = images_parser.parse_args()
        session = db_session.create_session()
        image = Image()
        image.name = args.get('name')
        if args.get('room_id'):
            room = session.query(Room).filter(Room.id == args.get('room_id')).first()
            if room:
                if room.image_count < config.room_image_limit:
                    image.room_id = room.id
                    image.room = room
                    room.image_count += 1
                else:
                    raise exceptions.Forbidden  # временно
            else:
                raise exceptions.NotFound
        image.generate_path()
        file = base64.b64decode(args.get('image_data'))
        img = PilImage.open(BytesIO(file))
        img.save(f'{image.path}.jpg')  # необходимо вместе с картинкой подавать сюда в .json и расширение!
        session.add(image)
        session.commit()
        return jsonify({'success': 'OK'})
