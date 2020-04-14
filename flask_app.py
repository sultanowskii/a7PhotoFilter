from random import randint

from flask_restful import Api
from flask import Flask
from flask import make_response
from flask import jsonify

from data.images import Image
from data.rooms import Room
from data.users import User
from data import users_resource
from data import images_resource
from data import rooms_resource
from data import db_session
from data.key_generator import generate_key
import config

from werkzeug import exceptions

app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = config.key


def main():
    api.add_resource(users_resource.UsersListResource, '/api/users')
    api.add_resource(users_resource.UsersResource, '/api/users/<int:user_id>')
    api.add_resource(rooms_resource.RoomsListResource, '/api/rooms')
    api.add_resource(rooms_resource.RoomsResource, '/api/rooms/<int:room_id>')
    api.add_resource(images_resource.ImagesListResource, '/api/images')
    api.add_resource(images_resource.ImagesResource, '/api/images/<int:image_id>')
    db_session.global_init("db/filter-bot.sqlite")
    app.run()


@app.errorhandler(exceptions.NotFound)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(exceptions.BadRequest)
def not_found(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)


if __name__ == "__main__":  # убери на сервере
    main()
