from flask_restful import Api
from flask import Flask
from flask import make_response
from flask import jsonify
import logging

from data import db_session, images_resource, rooms_resource, users_resource
import config
from werkzeug import exceptions

logging.basicConfig(
    filename='logs.log',
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    level=logging.INFO
)


app = Flask(__name__)
app.config['SECRET_KEY'] = config.KEY
api = Api(app)


def main():
    api.add_resource(users_resource.UsersListResource, '/api/users')
    api.add_resource(users_resource.UsersResource, '/api/users/<int:user_id>')
    api.add_resource(rooms_resource.RoomsListResource, '/api/rooms')
    api.add_resource(rooms_resource.RoomsResource, '/api/rooms/<int:room_id>')
    api.add_resource(images_resource.ImagesListResource, '/api/images')
    api.add_resource(images_resource.ImagesResource, '/api/images/<int:image_id>')
    try:
        db_session.global_init("db/data.sqlite")
    except Exception as e:
        logging.fatal(f'Error in database connection! Error: {e}')
        exit(-1)
    app.run()


if __name__ == "__main__":  # убери на сервере
    main()
