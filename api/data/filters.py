from .images import Image
from werkzeug import exceptions
from PIL import ImageFilter
from PIL import Image
from random import random


def add_filter(image_object, fid, mime):
    im = Image.open(f'{image_object.path}.{mime}')
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
    elif fid == 8:
        reducing_the_quality(pixels, x, y)
        return im
    elif fid == 9:
        add_noise(pixels, x, y)
        return im
    elif fid == 10:
        brown(pixels, x, y)
        return im
    elif fid == 11:
        all_black_white(pixels, x, y)
        return im
    else:
        raise exceptions.NotFound


def color_inversion1(pixels, x, y):  # Другой мир 1 (1)
    for i in range(x):
        for j in range(y):
            r, g, b = pixels[i, j]
            pixels[i, j] = g, b, r


def color_inversion2(pixels, x, y):  # Другой Мир 2 (2)
    for i in range(x):
        for j in range(y):
            r, g, b = pixels[i, j]
            pixels[i, j] = b, r, g


def black_white(pixels, x, y):  # Чёрно-белое (3)
    for i in range(x):
        for j in range(y):
            r, g, b = pixels[i, j]
            bw = (r + g + b) // 3
            pixels[i, j] = bw, bw, bw


def inversion(pixels, x, y):  # негатив (4)
    for i in range(x):
        for j in range(y):
            r, g, b = pixels[i, j]
            pixels[i, j] = 255 - r, 255 - g, 255 - b


def highlighting(pixels, x, y):  # высветление (5)
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


def degradation(im):  # размытие (6)
    return im.filter(ImageFilter.BLUR)


def sharpness(im):  # увеличение резкости (7)
    return im.filter(ImageFilter.SHARPEN)


def reducing_the_quality(pixels, x, y):  # уменьшение качества (8)
    for k in range(x // 2):
        for l in range(y // 2):
            i = k * 2
            j = l * 2
            if j + 1 < y and i + 1 < x:
                sumr = 0
                sumg = 0
                sumb = 0
                for ii in range(i, i + 2):
                    for jj in range(j, j + 2):
                        r, g, b = pixels[ii, jj]
                        sumr += r
                        sumg += g
                        sumb += b
                sumr //= 4
                sumb //= 4
                sumg //= 4
                for ii in range(i, i + 2):
                    for jj in range(j, j + 2):
                        pixels[ii, jj] = sumr, sumg, sumb


def add_noise(pixels, x, y):  # добавление шума(9)
    factor = 70
    for i in range(x):
        for j in range(y):
            rand = random.randint(-factor, factor)
            r, g, b = pixels[i, j]
            r += rand
            g += rand
            b += rand
            if r < 0:
                r = 0
            if g < 0:
                g = 0
            if b < 0:
                b = 0
            if r > 255:
                r = 255
            if g > 255:
                g = 255
            if b > 255:
                b = 255
            pixels[i, j] = r, g, b


def brown(pixels, x, y):  # ретро (10)
    depth = 30
    for i in range(x):
        for j in range(y):
            r, g, b = pixels[i, j]
            S = (r + g + b) // 3
            r = S + depth * 2
            g = S + depth
            b = S
            if r > 255:
                r = 255
            if g > 255:
                g = 255
            if b > 255:
                b = 255
            pixels[i, j] = r, g, b


def all_black_white(pixels, x, y):  # чёрно-белое 2 (11)
    factor = 100
    for i in range(x):
        for j in range(y):
            r, g, b = pixels[i, j]
            S = r + g + b
            if S > (((255 + factor) // 2) * 3):
                r, g, b = 255, 255, 255
            else:
                r, g, b = 0, 0, 0
            pixels[i, j] = r, g, b
