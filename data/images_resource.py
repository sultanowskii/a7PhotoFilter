from . import db_session
from .images import Image
from flask import jsonify
from flask_restful import abort, Resource
from . import images_parser
from . import editor_parser
from werkzeug import exceptions
from data import filters
from datetime import datetime

parser = images_parser.parser

# Целиком доработай image, чтобы везде нормально работали файлы


class ImagesResource(Resource):
    def get(self, image_id):
        args = editor_parser.parser.parse_args()
        session = db_session.create_session()
        image = session.query(Image).get(image_id)  # image должен быть файлом
        if not image:
            raise exceptions.NotFound
        if args['action'] == 'applyfilter' and args['fid'] != 0:
            image = filters.add_filter('файл картинки', args['fid'])
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


class ImagesListResource(Resource):
    def get(self):
        session = db_session.create_session()
        images = session.query(Image).all()
        return jsonify({'Images': [item.to_dict(
            only=('id', 'image')) for item in images]})

    def post(self):
        args = images_parser.parser.parse_args()
        #  здесь создаем файл с картинкой
        session = db_session.create_session()
        if not args['name']:
            args['name'] = datetime.now().strftime('%H%M%S-%d%m%Y')  # генерируем имя с помощью текущего врмени и даты
        image = Image(name=args['name'])
        session.add(image)
        session.commit()
        return jsonify({'success': 'OK'})