from . import db_session
from flask_restful import abort
from .users import User
from .rooms import Room
from .images import Image

# В случае, если необходимо делать свои хэндлеры, импортируй во все ресурсы и везде юзай это


def abort_if_user_not_found(user_id):
    session = db_session.create_session()
    user = session.query(User).get(user_id)
    if not user:
        abort(404, message=f"User not found")


def abort_if_room_not_found(room_id):
    session = db_session.create_session()
    room = session.query(Room).get(room_id)
    if not room:
        abort(404, message=f"Room not found")


def abort_if_image_not_found(image_id):
    session = db_session.create_session()
    image = session.query(Image).get(image_id)
    if not image:
        abort(404, message=f"Image not found")

