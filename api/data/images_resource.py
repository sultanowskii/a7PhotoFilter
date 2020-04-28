from .images import Image
from .rooms import Room
from . import db_session
from . import filters
from . import images_parser
from .aborts import abort_if_filter_not_found, abort_if_room_is_full_of_images, abort_if_image_not_found
from .aborts import abort_if_room_not_found
import config

from flask import jsonify, request
from flask_restful import Resource, abort

import base64
from io import BytesIO
from PIL import Image as PilImage
from datetime import datetime
import os
import logging

images_parser = images_parser.parser

logging.basicConfig(
    filename='logs.log',
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    level=logging.INFO
)


class ImagesResource(Resource):
    def get(self, image_id):
        abort_if_image_not_found(image_id)
        args = request.args
        session = db_session.create_session()
        image = session.query(Image).get(image_id)  # image должен быть файлом
        name = image.name
        if args.get('action') == 'applyfilter' and args.get('fid'):
            abort_if_filter_not_found(int(request.args['fid']))
            try:
                res_image = filters.add_filter(image, request.args['fid'])
            except Exception as e:
                logging.error(f'During filtering Image with id {image_id} error in filters.py happened. Error: {e}')
                return jsonify({'error': e})
            now = datetime.now().strftime('%H%M%S-%d%m%Y')
            path = f'userdata/img/{now}.{image.mime.lower()}'
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
        else:
            with open(image.path, 'rb') as f:
                string_data = base64.b64encode(f.read()).decode('utf-8')
            return jsonify({'Image': {'id': image.id, 'data': string_data, 'name': image.name}})

    def delete(self, image_id):
        abort_if_image_not_found(image_id)
        session = db_session.create_session()
        image = session.query(Image).get(image_id)
        image.room = None
        image.room_id = None
        try:
            os.remove(image.path)
        except Exception:
            logging.warning(f'During removing Image with id {image.id} mistake found: No .path in current image')
            abort(404, error='Image file is not found')
        session.delete(image)
        session.commit()
        return jsonify({'success': 'OK'})

    def put(self, image_id):
        abort_if_image_not_found(image_id)
        session = db_session.create_session()
        image = session.query(Image).get(image_id)
        args = images_parser.parse_args()
        if args.get('name'):
            image.name = args.get('name')
        if args.get('room_id'):
            abort_if_room_not_found(args.get('room_id'))
            room = session.query(Room).filter(Room.id == args.get('room_id')).first()
            if args.get('remove_room') == True:
                image.room = None
                image.room_id = None
            else:
                abort_if_room_is_full_of_images(room.id)
                image.room_id = room.id
                image.room = room
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
        if args.get('remove_room') == True:
            e = 'Invalid json-data: remove_room is not allowed in POST'
            logging.warning(f'Bad request for /images/ got. Error: {e}')
            abort(400, error=f'Bad request: {e}')
        req_args = ['name', 'mime', 'image_data']
        for arg in req_args:
            if args.get(arg) == None:
                e = f'Invalid json-data: No required argument \'{arg}\' in json'
                logging.warning(f'Bad request for /images/ got. Error: {e}')
                abort(400, error=f'Bad request: {e}')
        image = Image()
        image.name = args.get('name')
        image.mime = args.get('mime')
        if args.get('room_id'):
            abort_if_room_not_found(args.get('room_id'))
            room = session.query(Room).filter(Room.id == args.get('room_id')).first()
            abort_if_room_is_full_of_images(room.id)
            image.room_id = room.id
            image.room = room
        image.generate_path()
        img = None
        try:
            file = base64.b64decode(args.get('image_data'))
            img = PilImage.open(BytesIO(file))
        except Exception:
            logging.warning('Invalid image-data got')
            abort(400, error='Invalid image data')
        session.add(image)
        session.commit()
        img.save(image.path)
        return jsonify({'success': 'OK', 'id': image.id})
