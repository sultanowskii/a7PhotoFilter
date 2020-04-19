from data.key_generator import generate_key
from random import randint

ROOM_IMAGE_LIMIT = 6
ROOM_USER_LIMIT = 6
USER_ROOM_LIMIT = 6
KEY = generate_key(randint(6, 12))
