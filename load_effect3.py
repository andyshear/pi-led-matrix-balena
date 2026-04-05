import sys
import json
import threading
import time
import os
from collections import deque
import queue
import numpy as np
from src.led_matrix1 import Matrix, pixel_height, pixel_width
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageChops

times_history = deque(maxlen=2)
times_queue = queue.Queue()

laps_by_rider = {}
_last_time_by_rider = {}

current_effect = None
effect_change_lock = threading.Lock()
matrix = Matrix()
stop_event = threading.Event()
current_effect_thread = None

FLASH_DELAY = 500
SCROLL_DELAY = 20
MESSAGE = "CAUTION"
FONT_SIZE = 8
FONT_PATH = "path/to/font.ttf"

race_timer_start_ms = None
race_timer_label = ""

PANEL_W = 16
PANEL_H = 16

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DUPLICATE_VERTICAL_STACK = os.environ.get("DUPLICATE_VERTICAL_STACK", "false").lower() == "true"

LOGICAL_WIDTH = pixel_width
LOGICAL_HEIGHT = pixel_height // 2 if DUPLICATE_VERTICAL_STACK else pixel_height


def set_current_effect(effect):
    global current_effect
    with effect_change_lock:
        current_effect = effect


def get_current_effect():
    with effect_change_lock:
        return current_effect


def safe_load_font(size: int):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for path in candidates:
        try:
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()

def safe_load_mono_font(size: int):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationMono-Bold.ttf",
    ]
    for path in candidates:
        try:
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
        except Exception:
            pass
    return safe_load_font(size)

def text_bbox(draw, text, font):
    try:
        return draw.textbbox((0, 0), text, font=font)
    except Exception:
        w, h = draw.textsize(text, font=font)
        return (0, 0, w, h)

def draw_text_centered(draw, text, y, font, fill, width):
    if not text:
        return
    bbox = text_bbox(draw, text, font)
    text_w = bbox[2] - bbox[0]
    x = max(0, (width - text_w) // 2)
    draw.text((x, y), text, font=font, fill=fill)

def marquee_offset_px(speed_px_per_sec=20):
    now_ms = int(time.time() * 1000)
    return round((now_ms / 1000.0) * speed_px_per_sec)

def draw_text_marquee(draw, text, y, font, fill, width, offset_x=0, gap=12):
    """
    Draw scrolling text across a fixed-width area.
    If text fits, it will be centered instead.
    """
    if not text:
        return

    bbox = text_bbox(draw, text, font)
    text_w = bbox[2] - bbox[0]

    # If it fits, just center it
    if text_w <= width:
        draw_text_centered(draw, text, y, font, fill, width)
        return

    # Repeat text with a gap so marquee loops cleanly
    full_text = text + " " * 4
    bbox2 = text_bbox(draw, full_text, font)
    loop_w = (bbox2[2] - bbox2[0]) + gap

    if loop_w <= 0:
        draw_text_centered(draw, text, y, font, fill, width)
        return

    scroll_x = -(offset_x % loop_w)

    # draw enough copies to cover display width
    x = scroll_x
    while x < width:
        draw.text((x, y), full_text, font=font, fill=fill)
        x += loop_w

def draw_text_centered_fixed(draw, text, y, font, fill, width, spacing=1):
    if not text:
        return

    char_widths = []
    total_w = 0

    for ch in text:
        bbox = text_bbox(draw, ch, font)
        ch_w = bbox[2] - bbox[0]
        char_widths.append(ch_w)
        total_w += ch_w

    if len(text) > 1:
        total_w += spacing * (len(text) - 1)

    x = max(0, (width - total_w) // 2)

    for i, ch in enumerate(text):
        draw.text((x, y), ch, font=font, fill=fill)
        x += char_widths[i] + spacing

ICON_MAP = {
    "aztec": os.path.join(BASE_DIR, "assets", "icons", "aztec.png"),
    "suika": os.path.join(BASE_DIR, "assets", "icons", "suika.png"),
    "manana": os.path.join(BASE_DIR, "assets", "icons", "manana.png"),
    "icon": os.path.join(BASE_DIR, "assets", "icons", "logo.png"),
}

def render_icon_frame(payload: dict):
    if hasattr(matrix, "set_enhance"):
        matrix.set_enhance(False)

    width, height = LOGICAL_WIDTH, LOGICAL_HEIGHT
    icon_key = str(payload.get("icon", "") or "").lower()

    path = ICON_MAP.get(icon_key)

    # print(f"[icon] BASE_DIR={BASE_DIR}")
    # print(f"[icon] icon_key={icon_key}")
    # print(f"[icon] resolved path={path}")
    # print(f"[icon] exists={os.path.exists(path) if path else False}")

    if not path:
        print(f"[icon] unknown icon: {icon_key}")
        return Image.new("RGB", (width, height), (0, 0, 0))

    return load_icon_image(path, width, height)

def load_icon_image(path, width, height):
    try:
        img = Image.open(path).convert("RGBA")

        # kill almost-white background pixels so they don't nuke the board
        px = img.load()
        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = px[x, y]
                if a == 0:
                    continue

                # near-white -> transparent
                if r > 235 and g > 235 and b > 235:
                    px[x, y] = (0, 0, 0, 0)
                # if r > 220 and g > 220 and b > 220:
                #     px[x, y] = (0, 0, 0, 0)

        # fit inside board with a little margin
        target_w = max(1, width - 4)
        target_h = max(1, height - 4)
        img.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)

        # small, controlled enhancement for icon mode only
        rgb = Image.new("RGB", img.size, (0, 0, 0))
        rgb.paste(img, (0, 0), img)

        # rgb = ImageEnhance.Color(rgb).enhance(1.20)
        # rgb = ImageEnhance.Contrast(rgb).enhance(1.10)
        # rgb = ImageEnhance.Color(rgb).enhance(1.30)
        # rgb = ImageEnhance.Contrast(rgb).enhance(1.15)
        # rgb = rgb.filter(ImageFilter.SHARPEN)
        rgb = ImageEnhance.Color(rgb).enhance(1.18)
        rgb = ImageEnhance.Contrast(rgb).enhance(1.08)
        rgb = rgb.filter(ImageFilter.SHARPEN)

        palette = Image.new("P", (1, 1))
        palette.putpalette([
            0, 0, 0,         # black
            255, 255, 255,   # white
            255, 0, 0,       # red
            255, 200, 0,     # yellow
            0, 255, 0,       # green
            0, 120, 255,     # blue
            255, 120, 0,     # orange
        ] + [0, 0, 0] * 249)

        # rgb = rgb.quantize(palette=palette, dither=Image.Dither.NONE).convert("RGB")


        # rgb = np.array(rgb)
        # rgb[rgb > 240] = 240
        # rgb = Image.fromarray(rgb)
        # optional second sharpen for super simple logos only
        # rgb = rgb.filter(ImageFilter.SHARPEN)

        canvas = Image.new("RGB", (width, height), (0, 0, 0))
        x = (width - rgb.width) // 2
        y = (height - rgb.height) // 2
        canvas.paste(rgb, (x, y))

        return canvas

    except Exception as e:
        print(f"[icon] failed to load {path}: {e}")
        return Image.new("RGB", (width, height), (0, 0, 0))

def draw_text_left(draw, text, x, y, font, fill):
    if not text:
        return
    draw.text((x, y), text, font=font, fill=fill)


def push_image_to_matrix(image):
    src_w, src_h = image.size

    # Normal mode: write exactly what was rendered
    if not DUPLICATE_VERTICAL_STACK:
        for x in range(src_w):
            for y in range(src_h):
                r, g, b = image.getpixel((x, y))
                matrix.pixel((x, y), (b, g, r))
        matrix.show()
        return

    # Duplicate-top-to-bottom mode:
    # expected physical panel = 48 x 96
    # logical rendered frame = 48 x 48
    half_h = pixel_height // 2

    for x in range(min(src_w, pixel_width)):
        for y in range(min(src_h, half_h)):
            r, g, b = image.getpixel((x, y))
            bgr = (b, g, r)

            # top half
            matrix.pixel((x, y), bgr)

            # bottom half duplicate
            matrix.pixel((x, y + half_h), bgr)

    matrix.show()

def effect_icon(initial_payload=None):
    payload = initial_payload if isinstance(initial_payload, dict) else {}

    while not stop_event.is_set() and get_current_effect() == 'icon':
        frame = render_icon_frame(payload)
        push_image_to_matrix(frame)

        matrix.delay(16)  # smooth like your other display


def effect_error(_payload=None):
    width = 16
    height = 16

    def draw_exclamation(color):
        for y in range(3, 10):
            matrix.pixel((7, y), color)
            matrix.pixel((8, y), color)
        for x, y in [(7, 12), (8, 12), (7, 13), (8, 13)]:
            matrix.pixel((x, y), color)

    def draw_border(color):
        for x in range(width):
            matrix.pixel((x, 0), color)
            matrix.pixel((x, height - 1), color)
        for y in range(height):
            matrix.pixel((0, y), color)
            matrix.pixel((width - 1, y), color)

    while not stop_event.is_set() and get_current_effect() == 'error':
        matrix.reset()
        draw_border((255, 0, 0))
        draw_exclamation((255, 255, 255))
        matrix.show()
        matrix.delay(180)

        if stop_event.is_set() or get_current_effect() != 'error':
            break

        matrix.reset((255, 0, 0))
        draw_exclamation((0, 0, 0))
        matrix.show()
        matrix.delay(180)

        if stop_event.is_set() or get_current_effect() != 'error':
            break

        matrix.reset()
        draw_exclamation((255, 0, 0))
        matrix.show()
        matrix.delay(180)

    print("Exiting error effect.")


def effect_caution(_payload=None):
    while not stop_event.is_set() and get_current_effect() == 'caution':
        matrix.reset(matrix.color('yellow'))
        width = 16
        height = 16

        for i in range(min(width, height)):
            matrix.pixel((i, i), (255, 0, 0))
            if i + 1 < height:
                matrix.pixel((i, i + 1), (255, 0, 0))
            x2 = width - 1 - i
            matrix.pixel((x2, i), (255, 0, 0))
            if x2 + 1 < width:
                matrix.pixel((x2 + 1, i), (255, 0, 0))

        matrix.show()
        matrix.delay(50)
        matrix.reset()

        for i in range(min(width, height)):
            matrix.pixel((i, i), (255, 0, 0))
            if i + 1 < height:
                matrix.pixel((i, i + 1), (255, 0, 0))
            x2 = width - 1 - i
            matrix.pixel((x2, i), (255, 0, 0))
            if x2 + 1 < width:
                matrix.pixel((x2 + 1, i), (255, 0, 0))

        matrix.show()
        matrix.delay(50)
    print("Exiting caution effect.")


def effect_caution_left(_payload=None):
    while not stop_event.is_set() and get_current_effect() == 'cautionLeft':
        matrix.reset(matrix.color('yellow'))
        width = 16
        height = 16
        arrow_height = 10
        start_x = 0

        for x_offset in range(arrow_height):
            current_x = start_x + x_offset
            if current_x < 0 or current_x >= width:
                continue
            if x_offset > 0:
                for y_offset in range(height // 2 - 1, height // 2 + 2):
                    matrix.pixel((current_x, y_offset), (255, 0, 0))

        arrowhead_depth = 5
        for x_offset in range(arrowhead_depth):
            for y_offset in range(height // 2 - x_offset, height // 2 + x_offset + 1):
                px = start_x + arrow_height - arrowhead_depth - x_offset + 8
                if 0 <= px < width and 0 <= y_offset < height:
                    matrix.pixel((px, y_offset), (255, 0, 0))

        matrix.show()
        matrix.delay(50)
        matrix.reset()

        for x_offset in range(arrow_height):
            current_x = start_x + x_offset
            if current_x < 0 or current_x >= width:
                continue
            if x_offset > 0:
                for y_offset in range(height // 2 - 1, height // 2 + 2):
                    matrix.pixel((current_x, y_offset), (255, 0, 0))

        for x_offset in range(arrowhead_depth):
            for y_offset in range(height // 2 - x_offset, height // 2 + x_offset + 1):
                px = start_x + arrow_height - arrowhead_depth - x_offset + 8
                if 0 <= px < width and 0 <= y_offset < height:
                    matrix.pixel((px, y_offset), (255, 0, 0))

        matrix.show()
        matrix.delay(50)
    print("Exiting cautionLeft effect.")


def effect_caution_right(_payload=None):
    while not stop_event.is_set() and get_current_effect() == 'cautionRight':
        matrix.reset(matrix.color('yellow'))
        width = 16
        height = 16
        arrow_height = 12
        start_x = 3

        for x_offset in range(arrow_height):
            current_x = start_x + x_offset
            if current_x < 0 or current_x >= width:
                continue
            if x_offset > 0:
                for y_offset in range(height // 2 - 1, height // 2 + 2):
                    matrix.pixel((current_x, y_offset), (255, 0, 0))

        arrowhead_depth = 5
        for x_offset in range(arrowhead_depth):
            for y_offset in range(height // 2 - x_offset, height // 2 + x_offset + 1):
                px = start_x + arrow_height - arrowhead_depth + x_offset - 8
                if 0 <= px < width and 0 <= y_offset < height:
                    matrix.pixel((px, y_offset), (255, 0, 0))

        matrix.show()
        matrix.delay(50)
        matrix.reset()

        for x_offset in range(arrow_height):
            current_x = start_x + x_offset
            if current_x < 0 or current_x >= width:
                continue
            if x_offset > 0:
                for y_offset in range(height // 2 - 1, height // 2 + 2):
                    matrix.pixel((current_x, y_offset), (255, 0, 0))

        for x_offset in range(arrowhead_depth):
            for y_offset in range(height // 2 - x_offset, height // 2 + x_offset + 1):
                px = start_x + arrow_height - arrowhead_depth + x_offset - 8
                if 0 <= px < width and 0 <= y_offset < height:
                    matrix.pixel((px, y_offset), (255, 0, 0))

        matrix.show()
        matrix.delay(50)
    print("Exiting cautionRight effect.")


def effect_clear(_payload=None):
    global stop_event
    if get_current_effect() == 'clear':
        matrix.reset()
        arrow_height = 10
        width, height = 16, 16
        start_y = 5
        for y_offset in range(arrow_height):
            current_y = start_y + y_offset
            if current_y < 0 or current_y >= height:
                continue
            if y_offset > 0:
                for x_offset in range(width // 2 - 1, width // 2 + 2):
                    matrix.pixel((x_offset, current_y), (0, 128, 0))

            arrowhead_depth = 5
            for y_offset2 in range(arrowhead_depth):
                for x_offset in range(width // 2 - y_offset2, width // 2 + y_offset2 + 1):
                    current_y_position = start_y - arrowhead_depth + y_offset2 + 1
                    if 0 <= current_y_position < height:
                        matrix.pixel((x_offset, current_y_position), (0, 128, 0))
        matrix.show()


def effect_clearAnimation(_payload=None):
    arrow_height = 10
    width, height = 16, 16
    scroll_speed = 50

    while not stop_event.is_set() and get_current_effect() == 'clearAnimation':
        for start_y in range(height, -arrow_height, -1):
            matrix.reset()

            for y_offset in range(arrow_height):
                current_y = start_y + y_offset
                if current_y < 0 or current_y >= height:
                    continue

                if y_offset > 0:
                    for x_offset in range(width // 2 - 1, width // 2 + 2):
                        matrix.pixel((x_offset, current_y), (0, 128, 0))

                arrowhead_depth = 5
                for y_offset2 in range(arrowhead_depth):
                    for x_offset in range(width // 2 - y_offset2, width // 2 + y_offset2 + 1):
                        current_y_position = start_y - arrowhead_depth + y_offset2 + 1
                        if 0 <= current_y_position < height:
                            matrix.pixel((x_offset, current_y_position), (0, 128, 0))

            matrix.show()
            matrix.delay(scroll_speed)


def effect_medical(_payload=None):
    while not stop_event.is_set() and get_current_effect() == 'medical':
        width = 16
        height = 16
        cross_thickness = max(1, min(width, height) // 8)

        matrix.reset(matrix.color('white'))
        vertical_start = height // 2 - cross_thickness // 2
        vertical_end = vertical_start + cross_thickness
        for y in range(vertical_start, vertical_end):
            for x in range(width):
                matrix.pixel((x, y), (255, 0, 0))

        horizontal_start = width // 2 - cross_thickness // 2
        horizontal_end = horizontal_start + cross_thickness
        for x in range(horizontal_start, horizontal_end):
            for y in range(height):
                matrix.pixel((x, y), (255, 0, 0))

        matrix.show()
        matrix.delay(500)

        matrix.reset(matrix.color('red'))
        for y in range(vertical_start, vertical_end):
            for x in range(width):
                matrix.pixel((x, y), (255, 255, 255))

        for x in range(horizontal_start, horizontal_end):
            for y in range(height):
                matrix.pixel((x, y), (255, 255, 255))

        matrix.show()
        matrix.delay(500)

    print("Exiting medical effect.")


def effect_lastLap(_payload=None):
    if get_current_effect() == 'lastLap':
        matrix.reset(matrix.color('white'))
        matrix.show()


def effect_off(_payload=None):
    if get_current_effect() == 'off':
        matrix.reset()
        matrix.show()


def effect_lastLapAnimation(_payload=None):
    while not stop_event.is_set() and get_current_effect() == 'lastLapAnimation':
        checker_size = 2
        width, height = 16, 16

        matrix.reset(matrix.color('white'))
        for y in range(height):
            for x in range(width):
                if (x // checker_size % 2 == 0) ^ (y // checker_size % 2 == 0):
                    matrix.pixel((x, y), (0, 0, 0))

        matrix.show()
        matrix.delay(1000)
        matrix.reset()

        for y in range(height):
            for x in range(width):
                if (x // checker_size % 2 == 0) ^ (y // checker_size % 2 == 0):
                    matrix.pixel((x, y), (255, 255, 255))

        matrix.show()
        matrix.delay(1000)


def handle_timer_cmd(payload: dict):
    global race_timer_start_ms, race_timer_label
    start_ms = payload.get("startMs", None)
    label = payload.get("label", "")
    if start_ms is None:
        race_timer_start_ms = None
        race_timer_label = ""
        print("[timer] cleared")
    else:
        race_timer_start_ms = int(start_ms)
        race_timer_label = str(label or "")
        print(f"[timer] startMs={race_timer_start_ms} label={race_timer_label}")


def effect_times(_initial_rider_data_ignored=None):
    def parse_quad(payload: str):
        parts = [p.strip() for p in payload.split('-')]
        if len(parts) != 4:
            raise ValueError(f"Invalid rider data format: {payload!r} (expected 4 fields)")
        return parts[0], parts[1], parts[2], parts[3]

    def record_seen(name: str, lap_time: str, laps_str: str):
        try:
            laps_val = int(str(laps_str))
        except Exception:
            laps_val = laps_by_rider.get(name, 0)
        laps_by_rider[name] = laps_val
        _last_time_by_rider[name] = lap_time

    WIDTH, HEIGHT = LOGICAL_WIDTH, LOGICAL_HEIGHT
    NUM_LANES = 5
    PANE_W = max(1, WIDTH // NUM_LANES)

    font = ImageFont.load_default()
    line_h = 8
    Y_OFFSET = -2
    NAME_Y = Y_OFFSET
    TIME_Y = NAME_Y + line_h

    IDLE_SLEEP_MS = 20
    ROTATE_INTERVAL_MS = 900

    rider_lane = {}
    next_lane_toggle = 0
    lane_roster = [[] for _ in range(NUM_LANES)]
    lane_active_idx = [0 for _ in range(NUM_LANES)]
    lane_next_rotate_at = [0 for _ in range(NUM_LANES)]
    rider_rec = {}

    def assign_lane_if_new(name: str, first_lane: int, last_lane: int):
        nonlocal next_lane_toggle
        if name in rider_lane:
            lane = rider_lane[name]
            if lane < first_lane or lane > last_lane:
                lane = first_lane + (next_lane_toggle % (last_lane - first_lane + 1))
                next_lane_toggle += 1
                rider_lane[name] = lane
            return lane

        span = (last_lane - first_lane + 1)
        lane = first_lane + (next_lane_toggle % span)
        next_lane_toggle += 1
        rider_lane[name] = lane
        if name not in lane_roster[lane]:
            lane_roster[lane].append(name)
        return lane

    def set_active_to(name: str, lane: int):
        try:
            idx = lane_roster[lane].index(name)
        except ValueError:
            lane_roster[lane].append(name)
            idx = len(lane_roster[lane]) - 1
        lane_active_idx[lane] = idx
        lane_next_rotate_at[lane] = int(time.time() * 1000) + ROTATE_INTERVAL_MS

    def fmt_mmss(total_ms: int) -> str:
        total_s = max(0, total_ms // 1000)
        m = total_s // 60
        s = total_s % 60
        return f"{m}:{s:02d}"

    while not stop_event.is_set() and get_current_effect() == 'times':
        now_ms = int(time.time() * 1000)
        timer_active = (race_timer_start_ms is not None)

        riders_first_lane = 1 if timer_active else 0
        riders_last_lane = NUM_LANES - 1

        while True:
            try:
                payload = times_queue.get_nowait()
            except queue.Empty:
                break
            try:
                bike, name, laps_str, lap_time = parse_quad(payload)
                record_seen(name, lap_time, laps_str)
                rider_rec[name] = (bike, name, laps_str, lap_time)

                lane = assign_lane_if_new(name, riders_first_lane, riders_last_lane)
                if name not in lane_roster[lane]:
                    lane_roster[lane].append(name)
                set_active_to(name, lane)
            except Exception as e:
                print(f"[times] Skip invalid rider_data={payload!r}: {e}")

        for lane in range(riders_first_lane, riders_last_lane + 1):
            if not lane_roster[lane]:
                continue
            if now_ms >= lane_next_rotate_at[lane]:
                lane_active_idx[lane] = (lane_active_idx[lane] + 1) % len(lane_roster[lane])
                lane_next_rotate_at[lane] = now_ms + ROTATE_INTERVAL_MS

        frame = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
        draw = ImageDraw.Draw(frame)

        if timer_active:
            elapsed_ms = now_ms - race_timer_start_ms
            t_str = fmt_mmss(elapsed_ms)
            pane_x0 = 0

            if race_timer_label:
                draw.text((pane_x0, NAME_Y), str(race_timer_label), font=font, fill=(80, 160, 255))
                draw.text((pane_x0, TIME_Y), t_str, font=font, fill=(255, 255, 255))
            else:
                draw.text((pane_x0, NAME_Y), t_str, font=font, fill=(255, 255, 255))

        for lane in range(riders_first_lane, riders_last_lane + 1):
            if not lane_roster[lane]:
                continue
            pane_x0 = lane * PANE_W
            active_name = lane_roster[lane][lane_active_idx[lane]]

            bike, nm, _laps_str, lap_time = rider_rec.get(active_name, ("", active_name, "", ""))
            num_color = get_bike_color(bike)
            time_color = (255, 255, 255)

            draw.text((pane_x0, NAME_Y), nm, font=font, fill=num_color)
            draw.text((pane_x0, TIME_Y), lap_time, font=font, fill=time_color)

        push_image_to_matrix(frame)
        matrix.delay(IDLE_SLEEP_MS)


def render_panel_test_frame(payload: dict):
    """
    Draw 1..9 centered in each 16x16 tile on a 48x48 board.
    This is for physical mapping verification only.
    """
    width, height = LOGICAL_WIDTH, LOGICAL_HEIGHT
    frame = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(frame)

    cols = max(1, width // PANEL_W)
    rows = max(1, height // PANEL_H)

    border_color = (25, 25, 25)
    digit_colors = [
        (255, 80, 80),
        (80, 255, 80),
        (80, 160, 255),
        (255, 200, 80),
        (255, 80, 255),
        (80, 255, 255),
        (255, 255, 255),
        (180, 255, 120),
        (255, 160, 160),
    ]

    tile_font = safe_load_font(14)

    panel_num = 1
    for row in range(rows):
        for col in range(cols):
            x0 = col * PANEL_W
            y0 = row * PANEL_H
            x1 = min(x0 + PANEL_W - 1, width - 1)
            y1 = min(y0 + PANEL_H - 1, height - 1)

            # tile border
            draw.rectangle((x0, y0, x1, y1), outline=border_color)

            label = str(panel_num)
            color = digit_colors[(panel_num - 1) % len(digit_colors)]

            bbox = text_bbox(draw, label, tile_font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]

            tx = x0 + max(0, (PANEL_W - tw) // 2)
            ty = y0 + max(0, (PANEL_H - th) // 2) - 1

            draw.text((tx, ty), label, font=tile_font, fill=color)

            panel_num += 1

    # optional crosshair at board center
    cx = width // 2
    cy = height // 2
    for dx in range(-1, 2):
        if 0 <= cx + dx < width:
            draw.point((cx + dx, cy), fill=(255, 255, 255))
    for dy in range(-1, 2):
        if 0 <= cy + dy < height:
            draw.point((cx, cy + dy), fill=(255, 255, 255))

    return frame


def render_start_gate_frame(payload: dict):
    width, height = LOGICAL_WIDTH, LOGICAL_HEIGHT
    now_ms = int(time.time() * 1000)

    mode = str(payload.get("mode", "raceInfo") or "raceInfo")
    line1 = str(payload.get("line1", "") or "")
    line2 = str(payload.get("line2", "") or "")
    line3 = str(payload.get("line3", "") or "")
    line4 = str(payload.get("line4", "") or "")
    value = str(payload.get("value", "") or "")
    label = str(payload.get("label", "") or "")
    show_timer = bool(payload.get("showTimer", False))
    timer_start_ms = payload.get("timerStartMs", None)

    if mode == "panelTest":
        return render_panel_test_frame(payload)

    if mode == "icon":
        if hasattr(matrix, "set_enhance"):
            matrix.set_enhance(False)
        return render_icon_frame(payload)
    
    if hasattr(matrix, "set_enhance"):
        matrix.set_enhance(True)

    frame = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(frame)

    # -----------------------------
    # BIG NUMBER MODE
    # -----------------------------
    if mode == "bigNumber":
        label_text = label
        value_text = value[:3]

        label_font = safe_load_font(10)
        value_font = safe_load_font(36)

        # top banner
        if label_text:
            draw_text_marquee(
                draw,
                label_text,
                -1,
                label_font,
                (255, 220, 80),
                width,
                offset_x=marquee_offset_px(16),
                gap=8,
            )

        bbox = text_bbox(draw, value_text, value_font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        x = max(0, (width - text_w) // 2)

        # Pull value much closer to the header
        # Smaller y = higher on screen
        y = 7

        draw.text((x, y), value_text, font=value_font, fill=(255, 255, 255))
        return frame

    # -----------------------------
    # RACE INFO / TIMER MODE
    # -----------------------------
    if show_timer and timer_start_ms is not None:
        try:
            elapsed_ms = max(0, now_ms - int(timer_start_ms))
        except Exception:
            elapsed_ms = 0
        total_s = elapsed_ms // 1000
        timer_line = f"{total_s // 60}:{total_s % 60:02d}"
    else:
        timer_line = line2 or ""

    # Keep the top line compact for a 48x48 board
    header_text = line1
    footer3 = line3.replace(" ", "")[:8]
    footer4 = line4.replace(" ", "")[:8]

    header_font = safe_load_font(10)
    timer_font = safe_load_mono_font(18)
    footer_font = safe_load_font(7)

    if header_text:
        draw_text_marquee(
            draw,
            header_text,
            -1,
            header_font,
            (255, 220, 80),
            width,
            offset_x=marquee_offset_px(16),
            gap=8,
        )

    if timer_line:
        bbox = text_bbox(draw, timer_line, timer_font)
        text_h = bbox[3] - bbox[1]

        middle_top = 15
        middle_h = 18
        y = middle_top + max(0, (middle_h - text_h) // 2) - 1

        draw_text_centered_fixed(
            draw,
            timer_line,
            y,
            timer_font,
            (255, 255, 255),
            width,
            spacing=0
        )

    if footer4:
        draw_text_centered(draw, footer4, 32, footer_font, (180, 180, 255), width)

    if footer3:
        draw_text_centered(draw, footer3, 40, footer_font, (0, 255, 0), width)

    return frame


def effect_startGateDisplay(initial_payload=None):
    payload = initial_payload if isinstance(initial_payload, dict) else {}

    while not stop_event.is_set() and get_current_effect() == 'startGateDisplay':
        frame = render_start_gate_frame(payload)
        push_image_to_matrix(frame)

        # ~60 FPS for smooth marquee / animation
        matrix.delay(16)


def effect_startGateCountdown(_payload=None):
    width, height = LOGICAL_WIDTH, LOGICAL_HEIGHT
    label_font = safe_load_font(max(10, int(height * 0.18)))
    big_font = safe_load_font(max(20, int(height * 0.75)))

    def render_text_frame(top_text, big_text, big_color):
        image = Image.new("RGB", (width, height), (0, 0, 0))
        draw = ImageDraw.Draw(image)

        if top_text:
            draw_text_centered(draw, top_text, 2, label_font, (80, 160, 255), width)

        bbox = text_bbox(draw, big_text, big_font)
        text_h = bbox[3] - bbox[1]
        y = max(0, (height - text_h) // 2)
        draw_text_centered(draw, big_text, y, big_font, big_color, width)
        push_image_to_matrix(image)

    if stop_event.is_set():
        return

    print("Start Gate Countdown: Showing 30")
    matrix.reset(matrix.color('black'))
    render_text_frame("", "30", (255, 255, 255))
    matrix.delay(25000)

    if stop_event.is_set() or get_current_effect() != 'startGateCountdown':
        return

    print("Start Gate Countdown: Showing 5")
    matrix.reset(matrix.color('black'))
    render_text_frame("", "5", (255, 0, 0))
    matrix.delay(5000)

    if stop_event.is_set() or get_current_effect() != 'startGateCountdown':
        return

    print("Start Gate Countdown: Flashing green")
    for _ in range(3):
        matrix.reset((0, 255, 0))
        matrix.show()
        matrix.delay(300)
        matrix.reset((0, 0, 0))
        matrix.show()
        matrix.delay(300)

    matrix.reset((0, 0, 0))
    matrix.show()


def get_bike_color(bike_name):
    bike_colors = {
        'beta': (135, 206, 250),
        'gasgas': (255, 0, 0),
        'honda': (255, 0, 0),
        'husqvarna': (255, 255, 255),
        'ktm': (255, 140, 0),
        'kawasaki': (0, 255, 0),
        'stark': (255, 0, 0),
        'suzuki': (255, 255, 0),
        'yamaha': (80, 160, 255)
    }
    return bike_colors.get(str(bike_name).lower(), (255, 255, 255))


effects = {
    'caution': effect_caution,
    'cautionRight': effect_caution_right,
    'cautionLeft': effect_caution_left,
    'clearAnimation': effect_clearAnimation,
    'clear': effect_clear,
    'medical': effect_medical,
    'lastLapAnimation': effect_lastLapAnimation,
    'lastLap': effect_lastLap,
    'off': effect_off,
    'times': effect_times,
    'timer': handle_timer_cmd,
    'startGateCountdown': effect_startGateCountdown,
    'startGateDisplay': effect_startGateDisplay,
    'icon': effect_icon,
    'error': effect_error,
}


def apply_effect(effect_name, payload=None):
    global stop_event, current_effect_thread

    if effect_name == 'times' and get_current_effect() == 'times' and current_effect_thread is not None and current_effect_thread.is_alive():
        if isinstance(payload, str) and payload:
            times_queue.put(payload)
        return

    if current_effect_thread is not None:
        stop_event.set()
        current_effect_thread.join()
        stop_event.clear()

    set_current_effect(effect_name)
    current_effect_thread = threading.Thread(target=effects[effect_name], args=(payload,))
    current_effect_thread.start()

    if effect_name == 'times' and isinstance(payload, str) and payload:
        times_queue.put(payload)


def listen_for_commands():
    while True:
        input_data = sys.stdin.readline().strip()

        if not input_data:
            continue

        try:
            data = json.loads(input_data)
            effect_name = data.get('effect', None)

            if effect_name == "timer":
                handle_timer_cmd(data)
                continue

            if effect_name == "startGateDisplay":
                apply_effect(effect_name, data)
                continue

            if effect_name == "icon":
                apply_effect(effect_name, data)
                continue

            rider_data = data.get('riderData', None)

            if effect_name and effect_name in effects:
                apply_effect(effect_name, rider_data)
            else:
                print(f"Unknown effect: {effect_name}")

        except json.JSONDecodeError:
            print("Invalid data received. Skipping...")


if __name__ == "__main__":
    listen_for_commands()