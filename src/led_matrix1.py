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

print("RAW_ENV PIXEL_WIDTH:", os.environ.get("PIXEL_WIDTH"))
print("RAW_ENV PIXEL_HEIGHT:", os.environ.get("PIXEL_HEIGHT"))

pixel_width = int(os.environ.get("PIXEL_WIDTH", cfg["pixel_width"]))
pixel_height = int(os.environ.get("PIXEL_HEIGHT", cfg["pixel_height"]))

brightness = float(os.environ.get("BRIGHTNESS", cfg.get("brightness", 0.9)))
contrast = float(os.environ.get("CONTRAST", cfg["contrast"]))
color = float(os.environ.get("COLOR", cfg["color"]))

virtual_framerate = int(os.environ.get("VIRTUAL_FRAMERATE", cfg["virtual_framerate"]))
playlist_delay = int(os.environ.get("PLAYLIST_DELAY", cfg["playlist_delay"]))

# --- tiled board config ---
TILE_W = int(os.environ.get("TILE_W", "16"))
TILE_H = int(os.environ.get("TILE_H", "16"))
TILE_COLS = int(os.environ.get("TILE_COLS", str(max(1, pixel_width // TILE_W))))
TILE_ROWS = int(os.environ.get("TILE_ROWS", str(max(1, pixel_height // TILE_H))))

# Physical tile chain order:
# 1 2 3
# 4 5 6
# 7 8 9
#
# This file assumes row-major tile order by default.
TILE_ORDER = os.environ.get("TILE_ORDER", "row-major").lower()

# Inside each tile, most 16x16 LED panels are serpentine by row.
TILE_SERPENTINE = os.environ.get("TILE_SERPENTINE", "true").lower() == "true"

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
        "TILE_W": TILE_W,
        "TILE_H": TILE_H,
        "TILE_COLS": TILE_COLS,
        "TILE_ROWS": TILE_ROWS,
        "TILE_ORDER": TILE_ORDER,
        "TILE_SERPENTINE": TILE_SERPENTINE,
    },
)

try:
    import board
    import neopixel
except ImportError:
    VIRTUAL_ENV = True

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
    return (int(time.time()) - start_time) < playlist_delay

def get_tile_index(tile_col: int, tile_row: int) -> int:
    tile_order = os.environ.get("TILE_ORDER", "row-major").lower()

    # 1 2 3 / 4 5 6 / 7 8 9
    if tile_order == "row-major":
        return tile_row * TILE_COLS + tile_col

    # 1 2 3 / 6 5 4 / 7 8 9
    if tile_order == "row-snake":
        if tile_row % 2 == 0:
            return tile_row * TILE_COLS + tile_col
        return tile_row * TILE_COLS + (TILE_COLS - 1 - tile_col)

    # 1 4 7 / 2 5 8 / 3 6 9
    if tile_order == "col-major":
        return tile_col * TILE_ROWS + tile_row

    # 1 6 7 / 2 5 8 / 3 4 9 style vertical snake
    if tile_order == "col-snake":
        if tile_col % 2 == 0:
            return tile_col * TILE_ROWS + tile_row
        return tile_col * TILE_ROWS + (TILE_ROWS - 1 - tile_row)

    # fallback
    return tile_row * TILE_COLS + tile_col

def transform_local_coords(local_x: int, local_y: int):
    """
    Rotate/flip coordinates INSIDE a single 16x16 tile before strip mapping.
    Useful when tile placement is correct but each tile is rotated.
    """
    panel_rotation = os.environ.get("PANEL_ROTATION", "none").lower()

    # no rotation
    if panel_rotation == "none":
        return local_x, local_y

    # rotate logical image 90 CW before mapping
    # use this if displayed output appears 90 CCW
    if panel_rotation == "cw":
        return (TILE_W - 1 - local_y), local_x

    # rotate logical image 90 CCW before mapping
    if panel_rotation == "ccw":
        return local_y, (TILE_H - 1 - local_x)

    # rotate 180
    if panel_rotation == "180":
        return (TILE_W - 1 - local_x), (TILE_H - 1 - local_y)

    return local_x, local_y

def logical_xy_to_strip_index(x: int, y: int) -> int:
    tile_col = x // TILE_W
    tile_row = y // TILE_H

    local_x = x % TILE_W
    local_y = y % TILE_H

    # rotate inside each individual tile if needed
    local_x, local_y = transform_local_coords(local_x, local_y)

    tile_index = get_tile_index(tile_col, tile_row)

    panel_mode = os.environ.get("PANEL_MODE", "row_serp_tl").lower()

    # row serpentine, starts top-left
    if panel_mode == "row_serp_tl":
        if local_y % 2 == 0:
            local_index = local_y * TILE_W + local_x
        else:
            local_index = local_y * TILE_W + (TILE_W - 1 - local_x)

    # row serpentine, starts top-right
    elif panel_mode == "row_serp_tr":
        if local_y % 2 == 0:
            local_index = local_y * TILE_W + (TILE_W - 1 - local_x)
        else:
            local_index = local_y * TILE_W + local_x

    # row serpentine, starts bottom-left
    elif panel_mode == "row_serp_bl":
        flip_y = (TILE_H - 1 - local_y)
        if flip_y % 2 == 0:
            local_index = flip_y * TILE_W + local_x
        else:
            local_index = flip_y * TILE_W + (TILE_W - 1 - local_x)

    # row serpentine, starts bottom-right
    elif panel_mode == "row_serp_br":
        flip_y = (TILE_H - 1 - local_y)
        if flip_y % 2 == 0:
            local_index = flip_y * TILE_W + (TILE_W - 1 - local_x)
        else:
            local_index = flip_y * TILE_W + local_x

    # column serpentine, starts top-left
    elif panel_mode == "col_serp_tl":
        if local_x % 2 == 0:
            local_index = local_x * TILE_H + local_y
        else:
            local_index = local_x * TILE_H + (TILE_H - 1 - local_y)

    # column serpentine, starts top-right
    elif panel_mode == "col_serp_tr":
        flip_x = (TILE_W - 1 - local_x)
        if flip_x % 2 == 0:
            local_index = flip_x * TILE_H + local_y
        else:
            local_index = flip_x * TILE_H + (TILE_H - 1 - local_y)

    # column serpentine, starts bottom-left
    elif panel_mode == "col_serp_bl":
        if local_x % 2 == 0:
            local_index = local_x * TILE_H + (TILE_H - 1 - local_y)
        else:
            local_index = local_x * TILE_H + local_y

    # column serpentine, starts bottom-right
    elif panel_mode == "col_serp_br":
        flip_x = (TILE_W - 1 - local_x)
        if flip_x % 2 == 0:
            local_index = flip_x * TILE_H + (TILE_H - 1 - local_y)
        else:
            local_index = flip_x * TILE_H + local_y

    else:
        if local_y % 2 == 0:
            local_index = local_y * TILE_W + local_x
        else:
            local_index = local_y * TILE_W + (TILE_W - 1 - local_x)

    return tile_index * (TILE_W * TILE_H) + local_index


class VirtualMatrix():
    def __init__(self):
        self.frame = []
        self.reset()
        self.start_time = int(time.time())
        self.use_enhance = True

        print(
            "VIRTUAL_MATRIX_INIT",
            {
                "width": pixel_width,
                "height": pixel_height,
                "tile_w": TILE_W,
                "tile_h": TILE_H,
                "tile_cols": TILE_COLS,
                "tile_rows": TILE_ROWS,
                "tile_order": TILE_ORDER,
                "tile_serpentine": TILE_SERPENTINE,
                "num_pixels": pixel_width * pixel_height,
            },
        )

    def ready(self):
        return ready(self.start_time)

    def color(self, color_name):
        return colors.MAP[color_name]

    def random_color(self):
        return random_color()

    def image(self, img):
        rgb_image = img.convert(RGB)
        self.frame = np.array(rgb_image)

    def set_enhance(self, enabled: bool):
        self.use_enhance = bool(enabled)

    def show(self):
        frame = self.frame
        if self.use_enhance:
            frame = enhance(frame)

        frame = cv2.resize(
            frame,
            (pixel_width * VIRTUAL_SIZE_MULTIPLIER, pixel_height * VIRTUAL_SIZE_MULTIPLIER)
        )
        cv2.imshow('LED matrix', frame)
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
            pixel_order=neopixel.GRB,
        )

def pixels_front():
    if not VIRTUAL_ENV:
        return neopixel.NeoPixel(
            board.D18,
            pixel_width * pixel_height,
            brightness=brightness,
            auto_write=False,
            pixel_order=neopixel.GRB,
        )

def pixels_back():
    if not VIRTUAL_ENV:
        return neopixel.NeoPixel(
            board.D21,  # example, replace with your chosen second pin
            pixel_width * pixel_height,
            brightness=brightness,
            auto_write=False,
            pixel_order=neopixel.GRB,
        )

class LiveMatrix():
    def __init__(self):
        self.frame = []
        self.reset()
        self.pixels_front = pixels_front()
        self.pixels_back = pixels_back()
        self.start_time = int(time.time())
        self.use_enhance = True

        print("PANEL_MODE:", os.environ.get("PANEL_MODE", "row_serp_tl"))
        print("PANEL_ROTATION:", os.environ.get("PANEL_ROTATION", "none"))
        print(
            "LIVE_MATRIX_INIT",
            {
                "width": pixel_width,
                "height": pixel_height,
                "tile_w": TILE_W,
                "tile_h": TILE_H,
                "tile_cols": TILE_COLS,
                "tile_rows": TILE_ROWS,
                "tile_order": TILE_ORDER,
                "tile_serpentine": TILE_SERPENTINE,
                "num_pixels": pixel_width * pixel_height,
            },
        )

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

    def set_enhance(self, enabled: bool):
        self.use_enhance = bool(enabled)

    def show(self):
        frame_to_show = enhance(self.frame) if self.use_enhance else self.frame

        for y in range(pixel_height):
            for x in range(pixel_width):
                b, g, r = frame_to_show[y, x]
                idx = logical_xy_to_strip_index(x, y)
                if 0 <= idx < len(self.pixels_front):
                    rgb = (int(r), int(g), int(b))
                    self.pixels_front[idx] = rgb
                    self.pixels_back[idx] = rgb

        self.pixels_front.show()
        self.pixels_back.show()

    def text(self, message, start, font_size, rgb_color, font='dosis.ttf'):
        text(self, message, start, font_size, rgb_color, font)


def Matrix():
    if not VIRTUAL_ENV:
        return LiveMatrix()
    return VirtualMatrix()