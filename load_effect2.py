import sys
import json
import threading
import time
import os
from collections import deque
import queue

from src.led_matrix import Matrix, pixel_height, pixel_width
from PIL import Image, ImageDraw, ImageFont

times_history = deque(maxlen=2)     # [(bike, name, time)]
times_queue = queue.Queue()         # push rider payloads here

laps_by_rider = {}                  # rider_name -> lap count
_last_time_by_rider = {}            # rider_name -> last seen time (to avoid double-increment)

# Initialize global variables for effect control
current_effect = None
effect_change_lock = threading.Lock()
matrix = Matrix()
stop_event = threading.Event()
current_effect_thread = None

# Define the delay for flashing and scrolling
FLASH_DELAY = 500  # milliseconds
SCROLL_DELAY = 20  # milliseconds
MESSAGE = "CAUTION"
FONT_SIZE = 8
FONT_PATH = "path/to/font.ttf"

# ---- race timer state (shared across effects) ----
race_timer_start_ms = None   # epoch ms or None when off
race_timer_label = ""        # e.g. "M1" or "PRACT"


def set_current_effect(effect):
    global current_effect
    with effect_change_lock:
        current_effect = effect


def get_current_effect():
    with effect_change_lock:
        return current_effect


def safe_load_font(size: int):
    """
    Try a few common fonts; fall back to PIL default.
    """
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


def text_bbox(draw, text, font):
    """
    PIL compatibility helper.
    """
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


def draw_text_left(draw, text, x, y, font, fill):
    if not text:
        return
    draw.text((x, y), text, font=font, fill=fill)


def push_image_to_matrix(image):
    width, height = image.size
    for x in range(width):
        for y in range(height):
            matrix.pixel((x, y), image.getpixel((x, y)))
    matrix.show()


def effect_error(_payload=None):
    """System fault / reset required."""
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
    """Red, yellow, repeat."""
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
    """
    160x16 scoreboard mode.
    If race timer is active, Lane 0 shows timer and riders occupy lanes 1..4.
    Otherwise riders occupy all 5 lanes.

    Payload from Node for riders: "bike-#RIDERNUM-laps-lapTime"
    Timer control comes via {"effect":"timer","startMs":<epoch_ms>|null,"label":"..."}.
    """
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

    WIDTH, HEIGHT = pixel_width, pixel_height
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


def render_start_gate_frame(payload: dict):
    """
    Full-board renderer for the new start gate display.
    Intended for 48x48 on the new 3x3 panel layout.
    """
    WIDTH, HEIGHT = pixel_width, pixel_height
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

    frame = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    draw = ImageDraw.Draw(frame)

    # --- Mode: bigNumber ---
    if mode == "bigNumber":
        label_font = safe_load_font(max(8, HEIGHT // 6))
        value_font = safe_load_font(max(18, int(HEIGHT * 0.62)))

        if label:
            draw_text_centered(draw, label, 1, label_font, (80, 160, 255), WIDTH)

        bbox = text_bbox(draw, value, value_font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = max(0, (WIDTH - text_w) // 2)
        y = max(10, (HEIGHT - text_h) // 2 - 2)
        draw.text((x, y), value, font=value_font, fill=(255, 255, 255))
        return frame

    # --- Mode: raceInfo ---
    if show_timer and timer_start_ms is not None:
        try:
            elapsed_ms = max(0, now_ms - int(timer_start_ms))
        except Exception:
            elapsed_ms = 0
        total_s = elapsed_ms // 1000
        timer_line = f"{total_s // 60}:{total_s % 60:02d}"
    else:
        timer_line = line2

    # dynamic fonts for 48x48-ish canvas
    header_font = safe_load_font(max(8, HEIGHT // 6))
    timer_font = safe_load_font(max(14, int(HEIGHT * 0.34)))
    footer_font = safe_load_font(max(8, HEIGHT // 7))

    # top line
    draw_text_centered(draw, line1, 1, header_font, (80, 160, 255), WIDTH)

    # middle timer / main line
    bbox = text_bbox(draw, timer_line, timer_font)
    text_h = bbox[3] - bbox[1]
    middle_y = max(12, (HEIGHT - text_h) // 2 - 2)
    draw_text_centered(draw, timer_line, middle_y, timer_font, (255, 255, 255), WIDTH)

    # lower lines
    if line3:
        draw_text_centered(draw, line3, HEIGHT - 18, footer_font, (0, 255, 0), WIDTH)
    if line4:
        draw_text_centered(draw, line4, HEIGHT - 9, footer_font, (255, 255, 255), WIDTH)

    return frame


def effect_startGateDisplay(initial_payload=None):
    """
    New full-canvas mode for the start gate display.
    Supports:
      {
        "effect": "startGateDisplay",
        "mode": "raceInfo",
        "line1": "...",
        "line2": "...",
        "line3": "...",
        "line4": "...",
        "timerStartMs": 123,
        "showTimer": true
      }

    Or:
      {
        "effect": "startGateDisplay",
        "mode": "bigNumber",
        "value": "5",
        "label": "250B"
      }
    """
    payload = initial_payload if isinstance(initial_payload, dict) else {}
    last_render_key = None

    while not stop_event.is_set() and get_current_effect() == 'startGateDisplay':
        now_ms = int(time.time() * 1000)

        render_key = json.dumps({
            "payload": payload,
            "timerBucket": now_ms // 1000 if payload.get("showTimer") and payload.get("timerStartMs") is not None else None,
        }, sort_keys=True)

        if render_key != last_render_key:
            frame = render_start_gate_frame(payload)
            push_image_to_matrix(frame)
            last_render_key = render_key

        matrix.delay(80)


def effect_startGateCountdown(_payload=None):
    """
    Display '30', then '5', then flash green 3 times, then turn off.
    Scales to board size better than the old fixed 32x16 assumption.
    """
    width, height = pixel_width, pixel_height
    label_font = safe_load_font(max(10, height // 2))
    big_font = safe_load_font(max(18, int(height * 0.7)))

    def render_text_frame(top_text, big_text, big_color):
        image = Image.new("RGB", (width, height), (0, 0, 0))
        draw = ImageDraw.Draw(image)

        if top_text:
            draw_text_centered(draw, top_text, 1, label_font, (80, 160, 255), width)

        bbox = text_bbox(draw, big_text, big_font)
        text_h = bbox[3] - bbox[1]
        y = max(10, (height - text_h) // 2)
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
    'error': effect_error,
}


def apply_effect(effect_name, payload=None):
    global stop_event, current_effect_thread

    # Keep the existing scoreboard queue behavior
    if effect_name == 'times' and get_current_effect() == 'times' and current_effect_thread is not None and current_effect_thread.is_alive():
        if isinstance(payload, str) and payload:
            times_queue.put(payload)
        return

    # If already in startGateDisplay, just replace payload by restarting cleanly.
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
    """
    Continuously listen for new commands and apply effects accordingly.
    """
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

            rider_data = data.get('riderData', None)

            if effect_name and effect_name in effects:
                apply_effect(effect_name, rider_data)
            else:
                print(f"Unknown effect: {effect_name}")

        except json.JSONDecodeError:
            print("Invalid data received. Skipping...")


if __name__ == "__main__":
    listen_for_commands()