from . import db_session
from .images import Image
from .rooms import Room
from flask import jsonify, request
from flask_restful import Resource
from . import images_parser
from werkzeug import exceptions
from data import filters
from datetime import datetime

images_parser = images_parser.parser

# Целиком доработай image, чтобы везде нормально работали файлы
# Нуждается в полной доработке


class ImagesResource(Resource):
    def get(self, image_id):
        args = request.args
        session = db_session.create_session()
        image = session.query(Image).get(image_id)  # image должен быть файлом
        if not image:
            raise exceptions.NotFound
        if args.get('action') == 'applyfilter' and args.get('fid', None):
            image = filters.add_filter('файл картинки', request.args['fid'])
        return jsonify({'Image': image.to_dict(
            only=('id', 'name'))})

    def delete(self, image_id):
        session = db_session.create_session()
        image = session.query(Image).get(image_id)
        if not image:
            raise exceptions.NotFound
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
                    image.room = room
                    image.room_id = room.id
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
        #  здесь создаем файл с картинкой
        session = db_session.create_session()
        if not args['name']:
            args['name'] = datetime.now().strftime('%H%M%S-%d%m%Y')  # генерируем имя с помощью текущего врмени и даты
        image = Image(name=args.get('name'))
        session.add(image)
        session.commit()
        return jsonify({'success': 'OK'})
