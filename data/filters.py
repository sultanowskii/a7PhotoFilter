from .images import Image
from werkzeug import exceptions
from PIL import ImageFilter
from PIL import Image


def add_filter(image_object, fid):
    im = Image.open(image_object.path + ".jpg") #временно для тестов!!!!
    pixels = im.load()  # список с пикселями
    x, y = im.size
    fid = int(fid)
    if fid == 1:
        color_inversion1(pixels, x, y)
        return im
    elif fid == 2:
        color_inversion2(pixels, x, y)
        return im
    elif fid == 3:
        black_white(pixels, x, y)
        return im
    else:
        raise exceptions.NotFound


def color_inversion1(pixels, x, y):  #прикольная шняга 1
    for i in range(x):
        for j in range(y):
            r, g, b = pixels[i, j]
            pixels[i, j] = g, b, r


def color_inversion2(pixels, x, y):  #прикольная шняга 2
    for i in range(x):
        for j in range(y):
            r, g, b = pixels[i, j]
            pixels[i, j] = b, r, g


def black_white(pixels, x, y):   #Чёрно-белое
    for i in range(x):
        for j in range(y):
            r, g, b = pixels[i, j]
            bw = (r + g + b) // 3
            pixels[i, j] = bw, bw, bw
