from os.path import exists
import json
import random
import cv2
import time
import numpy as np
import os

from lib import colors
from PIL import ImageEnhance, Image, ImageDraw, ImageFont
from .lib import colors

CUSTOM_CONFIG = exists('config.json')
CONFIG = 'default_config.json' if not CUSTOM_CONFIG else 'config.json'

with open(CONFIG, mode='r', encoding='utf8') as j_object:
    cfg = json.load(j_object)

playlist = cfg['playlist']

# config and mapping for virtual env vs pi with LED matrix
VIRTUAL_ENV = False
VIRTUAL_SIZE_MULTIPLIER = 10

# size of matrix (allow balena env override)
print("RAW_ENV PIXEL_WIDTH:", os.environ.get("PIXEL_WIDTH"))
print("RAW_ENV PIXEL_HEIGHT:", os.environ.get("PIXEL_HEIGHT"))
print("RAW_ENV MATRIX_ORIENTATION:", os.environ.get("MATRIX_ORIENTATION"))

pixel_width = int(os.environ.get("PIXEL_WIDTH", cfg["pixel_width"]))
pixel_height = int(os.environ.get("PIXEL_HEIGHT", cfg["pixel_height"]))

# brightness 0 - 1 (allow balena env override)
brightness = float(os.environ.get("BRIGHTNESS", cfg.get("brightness", 0.9)))

# contrast/color can be overridable too if you want
contrast = float(os.environ.get("CONTRAST", cfg["contrast"]))
color = float(os.environ.get("COLOR", cfg["color"]))

virtual_framerate = int(os.environ.get("VIRTUAL_FRAMERATE", cfg["virtual_framerate"]))
playlist_delay = int(os.environ.get("PLAYLIST_DELAY", cfg["playlist_delay"]))

try:
    # live env
    import board
    import neopixel
    from adafruit_pixel_framebuf import PixelFramebuffer, VERTICAL, HORIZONTAL
except ImportError:
    # virtual env
    VIRTUAL_ENV = True
    # placeholders so logging below still works
    VERTICAL = "VERTICAL"
    HORIZONTAL = "HORIZONTAL"

# Orientation selection
# Your physical wiring is:
# 1 2 3
# 4 5 6
# 7 8 9
#
# That strongly suggests HORIZONTAL is the correct default.
orientation_name = os.environ.get("MATRIX_ORIENTATION", "HORIZONTAL").upper()
if orientation_name == "VERTICAL":
    matrix_orientation = VERTICAL
else:
    matrix_orientation = HORIZONTAL
    orientation_name = "HORIZONTAL"

print(
    "CONFIG_RESOLVED",
    {
        "CONFIG_FILE": CONFIG,
        "PIXEL_WIDTH": pixel_width,
        "PIXEL_HEIGHT": pixel_height,
        "BRIGHTNESS": brightness,
        "CONTRAST": contrast,
        "COLOR": color,
        "VIRTUAL_FRAMERATE": virtual_framerate,
        "PLAYLIST_DELAY": playlist_delay,
        "VIRTUAL_ENV": VIRTUAL_ENV,
        "MATRIX_ORIENTATION": orientation_name,
    },
)

pixel_pin = board.D18 if not VIRTUAL_ENV else 0
RGB = 'RGB'


def delay(self, ms):
    time.sleep(ms / 1000.0)


def reset(rgb_color):
    r, g, b = rgb_color
    return np.full([pixel_height, pixel_width, 3], [b, g, r], np.uint8)


def enhance(image):
    rgb_image = Image.fromarray(image, mode=RGB)
    color_enhance = ImageEnhance.Color(rgb_image)
    colored_image = color_enhance.enhance(color)
    contrast_enhancer = ImageEnhance.Contrast(colored_image)
    contrasted_image = contrast_enhancer.enhance(contrast)
    return np.array(contrasted_image)


def swap_rgb_to_bgr(rgb_color):
    r, g, b = rgb_color
    return (b, g, r)


def sprite(self, sprite_map, start, color_map):
    for y, line in enumerate(sprite_map):
        for x, pixel in enumerate(line):
            start_x, start_y = start
            if pixel != ' ':
                self.pixel((start_x + x, start_y + y), color_map[pixel])


def text(self, message, start, font_size, rgb_color, ttf_file):
    image = Image.fromarray(self.frame)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype('./fonts/' + ttf_file, font_size)
    draw.text(start, message, font=font, fill=(rgb_color))
    self.image(image)


def random_color():
    return (random.randrange(255), random.randrange(255), random.randrange(255))


def ready(start_time):
    if (int(time.time()) - start_time) < playlist_delay:
        return True
    return False


class VirtualMatrix():
    def __init__(self):
        self.frame = []
        self.reset()
        self.start_time = int(time.time())

    def ready(self):
        return ready(self.start_time)

    def color(self, color_name):
        return colors.MAP[color_name]

    def random_color(self):
        return random_color()

    def image(self, img):
        rgb_image = img.convert(RGB)
        self.frame = np.array(rgb_image)

    def show(self):
        frame = cv2.resize(
            self.frame,
            (pixel_width * VIRTUAL_SIZE_MULTIPLIER, pixel_height * VIRTUAL_SIZE_MULTIPLIER)
        )
        cv2.imshow('LED matrix', enhance(frame))
        cv2.waitKey(virtual_framerate)

    def reset(self, rgb_color=(0, 0, 0)):
        self.frame = reset(rgb_color)

    def delay(self, ms):
        time.sleep(ms / 1000.0)

    def line(self, start, end, rgb_color, width):
        cv2.line(self.frame, start, end, swap_rgb_to_bgr(rgb_color), width)

    def pixel(self, start, rgb_color):
        cv2.line(self.frame, start, start, swap_rgb_to_bgr(rgb_color), 1)

    def rectangle(self, start, end, rgb_color, width):
        cv2.rectangle(self.frame, start, end, swap_rgb_to_bgr(rgb_color), width)

    def circle(self, center, radius, rgb_color, width):
        cv2.circle(self.frame, center, radius, swap_rgb_to_bgr(rgb_color), width)

    def text(self, message, start, font_size, rgb_color, font='dosis.ttf'):
        text(self, message, start, font_size, swap_rgb_to_bgr(rgb_color), font)

    def sprite(self, sprite_map, start, color_map):
        sprite(self, sprite_map, start, color_map)


def pixels():
    if not VIRTUAL_ENV:
        return neopixel.NeoPixel(
            pixel_pin,
            pixel_width * pixel_height,
            brightness=brightness,
            auto_write=False,
        )


class LiveMatrix():
    def __init__(self):
        self.frame = []
        self.reset()
        neopixel_pixels = pixels()

        print(
            "PIXEL_FRAMEBUFFER_INIT",
            {
                "width": pixel_width,
                "height": pixel_height,
                "orientation": orientation_name,
            },
        )

        self.buff = PixelFramebuffer(
            neopixel_pixels,
            pixel_width,
            pixel_height,
            orientation=matrix_orientation
        )
        self.start_time = int(time.time())

    def ready(self):
        return ready(self.start_time)

    def color(self, color_name):
        return colors.MAP[color_name]

    def random_color(self):
        return random_color()

    def reset(self, rgb_color=(0, 0, 0)):
        self.frame = reset(rgb_color)

    def image(self, img):
        rgb_image = img.convert(RGB)
        self.frame = np.array(rgb_image)

    def line(self, start, end, rgb_color, width):
        cv2.line(self.frame, start, end, rgb_color, width)

    def pixel(self, start, rgb_color):
        cv2.line(self.frame, start, start, rgb_color, 1)

    def rectangle(self, start, end, rgb_color, width):
        cv2.rectangle(self.frame, start, end, rgb_color, width)

    def circle(self, center, radius, rgb_color, width):
        cv2.circle(self.frame, center, radius, rgb_color, width)

    def delay(self, ms):
        time.sleep(ms / 1000.0)

    def sprite(self, sprite_map, start, color_map):
        sprite(self, sprite_map, start, color_map)

    def show(self):
        img = Image.fromarray(enhance(self.frame), mode=RGB)
        self.buff.image(img)
        self.buff.display()

    def text(self, message, start, font_size, rgb_color, font='dosis.ttf'):
        text(self, message, start, font_size, rgb_color, font)


def Matrix():  # pylint: disable=invalid-name
    if not VIRTUAL_ENV:
        return LiveMatrix()
    return VirtualMatrix()