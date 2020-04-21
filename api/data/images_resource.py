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
from datetime import datetime
import os
import logging

logging.basicConfig(
    filename='logs.log',
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)

images_parser = images_parser.parser


class ImagesResource(Resource):
    def get(self, image_id):
        args = request.args
        session = db_session.create_session()
        image = session.query(Image).get(image_id)  # image должен быть файлом
        name = image.name
        if not image:
            raise exceptions.NotFound
        if args.get('action') == 'applyfilter' and args.get('fid', None):
            try:
                res_image = filters.add_filter(image, request.args['fid'], image.mime)
            except Exception as e:
                logging.error(f'During filtering Image with id {image_id} error in filters.py happened. Error: {e}')
        else:
            res_image = PilImage.open(image.path)
        now = datetime.now().strftime('%H%M%S-%d%m%Y')
        path = f'static/img/{now}.{image.mime.lower()}'
        new_im = Image()
        new_im.path = path
        new_im.name = now
        new_im.mime = image.mime
        res_image.save(path)
        session.add(new_im)
        session.commit()
        with open(path, 'rb') as f:
            string_data = base64.b64encode(f.read()).decode('utf-8')
        return jsonify({'Image': {'id': new_im.id, 'data': string_data, 'name': name}})

    def delete(self, image_id):
        session = db_session.create_session()
        image = session.query(Image).get(image_id)
        if not image:
            raise exceptions.NotFound
        image.room = None
        image.room_id = None
        try:
            os.remove(image.path)
        except Exception:
            logging.warning(f'During removing Image with id {image.id} mistake found: No .path in current image')
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
        image.mime = args.get('mime')
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
        session.add(image)
        session.commit()
        img.save(image.path)
        return jsonify({'success': 'OK', 'id': image.id})
