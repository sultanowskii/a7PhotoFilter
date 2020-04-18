from data.key_generator import generate_key
from random import randint

ROOM_IMAGE_LIMIT = 10
ROOM_USER_LIMIT = 10
USER_ROOM_LIMIT = 10
KEY = generate_key(randint(6, 12))
