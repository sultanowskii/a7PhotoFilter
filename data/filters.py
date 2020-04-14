from .images import Image
from werkzeug import exceptions


def add_filter(image_object, fid):
    im = Image.open(image_object.path)
    if fid == 1:
        return im
    elif fid == 2:
        return im
    else:
        raise exceptions.NotFound
