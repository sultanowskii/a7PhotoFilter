from . import db_session
from flask_restful import abort
from .users import User
from .rooms import Room
from .images import Image
from .. import config


def abort_if_user_not_found(user_id):
    session = db_session.create_session()
    user = session.query(User).get(user_id)
    if not user:
        abort(404, error=f"User not found")


def abort_if_room_not_found(room_id):
    session = db_session.create_session()
    room = session.query(Room).get(room_id)
    if not room:
        abort(404, error=f"Room not found")


def abort_if_image_not_found(image_id):
    session = db_session.create_session()
    image = session.query(Image).get(image_id)
    if not image:
        abort(404, error=f"Image not found")


def abort_if_room_is_full_of_images(room_id):
    session = db_session.create_session()
    room = session.query(Image).get(room_id)
    if len(room.images) > config.ROOM_IMAGE_LIMIT:
        abort(403, error=f"Room {room_id} is full of images")


def abort_if_room_is_full_of_users(room_id):
    session = db_session.create_session()
    room = session.query(Image).get(room_id)
    if len(room.users) > config.ROOM_USER_LIMIT:
        abort(403, error=f"Room {room_id} is full of users")


def abort_if_user_is_full_of_rooms(user_id):
    session = db_session.create_session()
    user = session.query(Image).get(user_id)
    if len(user.rooms) > config.USER_ROOM_LIMIT:
        abort(403, error=f"User {user_id} is full of rooms")


def abort_if_filter_not_found(filter_id):
    if filter_id < 0 or filter_id > config.FILTERS_COUNT:
        abort(404, error=f"There is no filter with id {filter_id}")