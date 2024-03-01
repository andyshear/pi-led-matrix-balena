from os.path import exists
import json
import random
import time
import numpy as np

from lib import colors
from PIL import ImageEnhance, Image, ImageDraw, ImageFont

CUSTOM_CONFIG = exists('config.json')
CONFIG = 'default_config.json' if not CUSTOM_CONFIG else 'config.json'

with open(CONFIG, mode='r',  encoding='utf8') as j_object:
    cfg = json.load(j_object)

# size of matrix
pixel_width = cfg['pixel_width']
pixel_height = cfg['pixel_height']

# brightness 0 - 1
brightness = cfg['brightness']

# contrast (1 is no change)
contrast = cfg['contrast']

# color (1 is no change)
color = cfg['color']

# framerate between renderings in milliseconds in virtual mode
# this mimics the delay of hardware latency
virtual_framerate = cfg['virtual_framerate']

# playlists follow this format:
playlist = cfg['playlist']
playlist_delay = cfg['playlist_delay']

VIRTUAL_ENV = False

try:
    # live env
    import board
    import neopixel
    from adafruit_pixel_framebuf import PixelFramebuffer, VERTICAL
except ImportError:
    # Placeholder for environment detection
    VIRTUAL_ENV = True

pixel_pin = board.D18 if not VIRTUAL_ENV else 0
RGB = 'RGB'

def reset(rgb_color):
    r, g, b = rgb_color
    return np.full([pixel_height, pixel_width, 3],[b, g, r], np.uint8)

def enhance(image):
    rgb_image = Image.fromarray(image, mode=RGB)
    color_enhance = ImageEnhance.Color(rgb_image)
    colored_image = color_enhance.enhance(color)
    contrast_enhancer = ImageEnhance.Contrast(colored_image)
    contrasted_image =  contrast_enhancer.enhance(contrast)
    return np.array(contrasted_image)

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
    draw.text(start, message, font = font, fill = (rgb_color))
    self.image(image)

def random_color():
    return (random.randrange(255), random.randrange(255), random.randrange(255))

def ready(start_time):
    if (int(time.time()) - start_time) < playlist_delay:
        return True
    else:
        return False

class MatrixBase():
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

    def reset(self, rgb_color=(0, 0, 0)):
        self.frame = reset(rgb_color)

    def delay(self, ms):
        time.sleep(ms / 1000.0)  # Convert milliseconds to seconds

    def text(self, message, start, font_size, rgb_color, font='dosis.ttf'):
        text(self, message, start, font_size, rgb_color, font)

    def sprite(self, sprite_map, start, color_map):
        sprite(self, sprite_map, start, color_map)

class LiveMatrix(MatrixBase):
    def __init__(self):
        super().__init__()
        neopixel_pixels = pixels()
        self.buff = PixelFramebuffer(
            neopixel_pixels,
            pixel_width,
            pixel_height,
            orientation=VERTICAL
        )

    def show(self):
        img = Image.fromarray(enhance(self.frame), mode=RGB)
        self.buff.image(img)
        self.buff.display()

def pixels():
    if not VIRTUAL_ENV:
        return neopixel.NeoPixel(
            pixel_pin,
            pixel_width * pixel_height,
            brightness=brightness,
            auto_write=False,
        )

# Simplified matrix selection
def Matrix():  # pylint: disable=invalid-name
    return LiveMatrix() if not VIRTUAL_ENV else MatrixBase()
