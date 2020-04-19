from .images import Image
from .rooms import Room
from . import db_session
from . import filters
from . import images_parser
import config

from flask import jsonify, request
from flask_restful import Resource
from werkzeug import exceptions

import base64
from io import BytesIO
from PIL import Image as PilImage

images_parser = images_parser.parser


class ImagesResource(Resource):
    def get(self, image_id):
        args = request.args
        session = db_session.create_session()
        image = session.query(Image).get(image_id)  # image должен быть файлом
        name = image.name
        iid = image.id
        if not image:
            raise exceptions.NotFound
        if args.get('action') == 'applyfilter' and args.get('fid', None):
            res_image = filters.add_filter(image, request.args['fid'])
        else:
            res_image = PilImage.open(image.path)
        buf = BytesIO()
        res_image.save(buf, format='JPEG')
        byte_im = buf.getvalue()
        string_data = base64.b64encode(byte_im).decode('utf-8')
        return jsonify({'Image': {'id': iid, 'data': string_data, 'name': name}})

    def delete(self, image_id):
        session = db_session.create_session()
        image = session.query(Image).get(image_id)
        if not image:
            raise exceptions.NotFound
        image.room = None
        image.room_id = None
        session.delete(image)
        session.commit()
        return jsonify({'success': 'OK'})

    def put(self, image_id):
        session = db_session.create_session()
        image = session.query(Image).get(image_id)
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
                else:
                    if len(room.images) < config.ROOM_IMAGE_LIMIT:
                        image.room_id = room.id
                        image.room = room
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
        return jsonify({'images': [item.to_dict(
            only=('id', 'name')) for item in images]})

    def post(self):
        args = images_parser.parse_args()
        session = db_session.create_session()
        image = Image()
        image.name = args.get('name')
        if args.get('room_id'):
            room = session.query(Room).filter(Room.id == args.get('room_id')).first()
            if room:
                if len(room.images) < config.ROOM_IMAGE_LIMIT:
                    image.room_id = room.id
                    image.room = room
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
