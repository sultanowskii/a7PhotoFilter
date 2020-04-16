from .images import Image
from werkzeug import exceptions
from PIL import ImageFilter
from PIL import Image


def add_filter(image_object, fid):
    im = Image.open(image_object.path + ".jpg")  # временно для тестов!!!!
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
    elif fid == 4:
        inversion(pixels, x, y)
        return im
    elif fid == 5:
        highlighting(pixels, x, y)
        return im
    elif fid == 6:
        return degradation(im)
    elif fid == 7:
        return sharpness(im)
    else:
        raise exceptions.NotFound


def color_inversion1(pixels, x, y):  # прикольная шняга 1
    for i in range(x):
        for j in range(y):
            r, g, b = pixels[i, j]
            pixels[i, j] = g, b, r


def color_inversion2(pixels, x, y):  # прикольная шняга 2
    for i in range(x):
        for j in range(y):
            r, g, b = pixels[i, j]
            pixels[i, j] = b, r, g


def black_white(pixels, x, y):  # Чёрно-белое
    for i in range(x):
        for j in range(y):
            r, g, b = pixels[i, j]
            bw = (r + g + b) // 3
            pixels[i, j] = bw, bw, bw


def inversion(pixels, x, y):  # негатив
    for i in range(x):
        for j in range(y):
            r, g, b = pixels[i, j]
            pixels[i, j] = 255 - r, 255 - g, 255 - b


def highlighting(pixels, x, y):  # высветление
    def curve(pixel):
        r, g, b = pixel
        brightness = r + g + b
        if brightness < 60:
            if brightness == 0:
                k = 1
            else:
                k = 60 / brightness
            return min(255, int(r * k ** 2)), min(255, int(g * k ** 2)), \
                   min(255, int(b * k ** 2))
        else:
            return r, g, b

    for i in range(x):
        for j in range(y):
            pixels[i, j] = curve(pixels[i, j])


def degradation(im):  # размытие
    return im.filter(ImageFilter.BLUR)


def sharpness(im):  # увеличение резкости
    return im.filter(ImageFilter.SHARPEN)
