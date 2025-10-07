import sys
import json
import threading
from src.led_matrix import Matrix, pixel_height, pixel_width
from PIL import Image, ImageDraw, ImageFont
from collections import deque
# Optional override: 'auto' | 'wide16x64' | 'tall32x32'
FORCE_LAYOUT = 'auto'   # set to 'wide16x64' if you want to force side-by-side

# Initialize global variables for effect control
current_effect = None
effect_change_lock = threading.Lock()
matrix = Matrix()  # Initialize your matrix here
stop_event = threading.Event()  # Define the stop event here
current_effect_thread = None  # Keep a reference to the current effect thread

# Define the delay for flashing and scrolling
FLASH_DELAY = 500  # milliseconds for color change
SCROLL_DELAY = 20  # milliseconds for scroll speed
MESSAGE = "CAUTION"
FONT_SIZE = 8  # Adjust as needed
FONT_PATH = "path/to/font.ttf"  # Adjust the font path as necessary

# ====== WS2812 2x2 CONFIG (adjust if needed) ======
PANEL_W, PANEL_H = 16, 16
PANELS_X, PANELS_Y = 2, 2              # 2 columns x 2 rows -> 32x32 virtual
LEDS_PER_PANEL = PANEL_W * PANEL_H     # 256
TOTAL_LEDS = LEDS_PER_PANEL * PANELS_X * PANELS_Y  # 1024 (make sure your strip is init'd with this!)

# Panel chain order (index 0 = first panel from Pi's data-in).
# Default guess is TL -> TR -> BL -> BR. Change if your Test 2 colors don't match.
PANEL_ORDER = [
    (0, 0),  # panel 0: top-left
    (1, 0),  # panel 1: top-right
    (0, 1),  # panel 2: bottom-left
    (1, 1),  # panel 3: bottom-right
]

SERPENTINE_WITHIN_PANEL = True  # most 16x16 WS2812 matrices are serpentine by row

# --------- mapping helpers ---------
def _idx_local_16x16(lx, ly):
    if SERPENTINE_WITHIN_PANEL and (ly % 2 == 1):
        return ly * PANEL_W + (PANEL_W - 1 - lx)
    return ly * PANEL_W + lx

def _xy_to_panel_index(tile_x, tile_y):
    # PANEL_ORDER[k] == (tile_x, tile_y) -> returns k
    try:
        return PANEL_ORDER.index((tile_x, tile_y))
    except ValueError:
        return None

def _xy_to_linear(x, y):
    # which 16x16 tile?
    tile_x = x // PANEL_W
    tile_y = y // PANEL_H
    lx = x % PANEL_W
    ly = y % PANEL_H
    panel_idx = _xy_to_panel_index(tile_x, tile_y)
    if panel_idx is None:
        return None
    return panel_idx * LEDS_PER_PANEL + _idx_local_16x16(lx, ly)

def _put_pixel(matrix, x, y, color):
    # Try a coordinate API first (your earlier code had matrix.pixel((x,y), color))
    if hasattr(matrix, "pixel"):
        matrix.pixel((x, y), color)
        return
    # Else try linear (NeoPixel-like): matrix.setPixelColor / matrix[i] = color
    idx = _xy_to_linear(x, y)
    if idx is None:
        return
    if hasattr(matrix, "setPixelColor"):
        # r,g,b tuple -> packed color if needed
        r, g, b = color
        try:
            from rpi_ws281x import Color
            matrix.setPixelColor(idx, Color(r, g, b))
        except Exception:
            # fall back if Color not present
            matrix.setPixelColor(idx, (r << 16) | (g << 8) | b)
    else:
        # allow simple list-like interface
        try:
            matrix[idx] = color
        except Exception:
            pass

def _clear_matrix(matrix):
    # 32x32 virtual
    for y in range(PANEL_H * PANELS_Y):
        for x in range(PANEL_W * PANELS_X):
            _put_pixel(matrix, x, y, (0, 0, 0))

def set_current_effect(effect):
    global current_effect
    with effect_change_lock:
        current_effect = effect

def get_current_effect():
    with effect_change_lock:
        return current_effect

def effect_caution():
    """Red, yellow, repeat."""
    while not stop_event.is_set() and get_current_effect() == 'caution':
        matrix.reset(matrix.color('yellow'))
        
        # Define the size of the matrix
        width = 16
        height = 16
        
        # Draw 'X' by connecting opposite corners
        for i in range(min(width, height)):
            # Draw from top-left to bottom-right
            matrix.pixel((i, i), (255, 0, 0))
            matrix.pixel((i, i+1), (255, 0, 0))
            # Draw from top-right to bottom-left
            matrix.pixel((width - 1 - i, i), (255, 0, 0))
            matrix.pixel((width - 1 - i+1, i), (255, 0, 0))

        matrix.show()
        matrix.delay(50)
        matrix.reset()
        
        # Define the size of the matrix
        width = 16
        height = 16
        
        # Draw 'X' by connecting opposite corners
        for i in range(min(width, height)):
            # Draw from top-left to bottom-right
            matrix.pixel((i, i), (255, 0, 0))
            matrix.pixel((i, i+1), (255, 0, 0))
            # Draw from top-right to bottom-left
            matrix.pixel((width - 1 - i, i), (255, 0, 0))
            matrix.pixel((width - 1 - i+1, i), (255, 0, 0))

        matrix.show()
        matrix.delay(50)
    print("Exiting caution effect.")

def effect_caution_left():
    """Red, yellow, repeat."""
    while not stop_event.is_set() and get_current_effect() == 'cautionLeft':
        matrix.reset(matrix.color('yellow'))
        
        # Define the size of the matrix
        width = 16
        height = 16
        arrow_height = 10  # Adjusted for a larger arrow
        start_x = 0
        # Draw the arrow shaft (horizontal now)
        for x_offset in range(arrow_height):
            current_x = start_x + x_offset
            
            if current_x < 0 or current_x >= width:
                continue  # Skip drawing outside the matrix bounds

            # Shaft width
            if x_offset > 0:  # Skip the first few rows for the arrowhead
                for y_offset in range(height // 2 - 1, height // 2 + 2):  # Widen the shaft vertically
                    matrix.pixel((current_x, y_offset), (255, 0, 0))  # Red color for the arrow shaft

        # Draw the arrowhead (facing right now)
        arrowhead_depth = 5  # Depth of the arrowhead
        x_arrowhead = 5  # Depth of the arrowhead
        for x_offset in range(arrowhead_depth):
            # Calculate the width of the arrowhead at this level
            arrowhead_width = arrowhead_depth - x_offset
            for y_offset in range(height // 2 - x_offset, height // 2 + x_offset + 1):
                # Reverse the arrowhead direction from right to left
                matrix.pixel((start_x + arrow_height - arrowhead_depth - x_offset + 8, y_offset), (255, 0, 0))


        matrix.show()
        matrix.delay(50)
        matrix.reset()
        
        # Draw the arrow shaft (horizontal now)
        for x_offset in range(arrow_height):
            current_x = start_x + x_offset
            
            if current_x < 0 or current_x >= width:
                continue  # Skip drawing outside the matrix bounds

            # Shaft width
            if x_offset > 0:  # Skip the first few rows for the arrowhead
                for y_offset in range(height // 2 - 1, height // 2 + 2):  # Widen the shaft vertically
                    matrix.pixel((current_x, y_offset), (255, 0, 0))  # Red color for the arrow shaft

        # Draw the arrowhead (facing right now)
        arrowhead_depth = 5  # Depth of the arrowhead
        x_arrowhead = 5  # Depth of the arrowhead
        for x_offset in range(arrowhead_depth):
            # Calculate the width of the arrowhead at this level
            arrowhead_width = arrowhead_depth - x_offset
            for y_offset in range(height // 2 - x_offset, height // 2 + x_offset + 1):
                # Reverse the arrowhead direction from right to left
                matrix.pixel((start_x + arrow_height - arrowhead_depth - x_offset + 8, y_offset), (255, 0, 0))


        matrix.show()
        matrix.delay(50)
    print("Exiting caution effect.")

def effect_caution_right():
    """Red, yellow, repeat."""
    while not stop_event.is_set() and get_current_effect() == 'cautionRight':
        matrix.reset(matrix.color('yellow'))
        
        # Define the size of the matrix
        width = 16
        height = 16
        arrow_height = 12  # Adjusted for a larger arrow
        start_x = 3
        # Draw the arrow shaft (horizontal now)
        for x_offset in range(arrow_height):
            current_x = start_x + x_offset
            
            if current_x < 0 or current_x >= width:
                continue  # Skip drawing outside the matrix bounds

            # Shaft width
            if x_offset > 0:  # Skip the first few rows for the arrowhead
                for y_offset in range(height // 2 - 1, height // 2 + 2):  # Widen the shaft vertically
                    matrix.pixel((current_x, y_offset), (255, 0, 0))  # Red color for the arrow shaft

        # Draw the arrowhead (facing right now)
        arrowhead_depth = 5  # Depth of the arrowhead
        x_arrowhead = 5  # Depth of the arrowhead
        for x_offset in range(arrowhead_depth):
            # Calculate the width of the arrowhead at this level
            arrowhead_width = arrowhead_depth - x_offset
            for y_offset in range(height // 2 - x_offset, height // 2 + x_offset + 1):
                # Draw the arrowhead at the tip of the shaft (right end)
                matrix.pixel((start_x + arrow_height - arrowhead_depth + x_offset - 8, y_offset), (255, 0, 0))

        matrix.show()
        matrix.delay(50)
        matrix.reset()
        
        # Draw the arrow shaft (horizontal now)
        for x_offset in range(arrow_height):
            current_x = start_x + x_offset
            
            if current_x < 0 or current_x >= width:
                continue  # Skip drawing outside the matrix bounds

            # Shaft width
            if x_offset > 0:  # Skip the first few rows for the arrowhead
                for y_offset in range(height // 2 - 1, height // 2 + 2):  # Widen the shaft vertically
                    matrix.pixel((current_x, y_offset), (255, 0, 0))  # Red color for the arrow shaft

        # Draw the arrowhead (facing right now)
        arrowhead_depth = 5  # Depth of the arrowhead
        x_arrowhead = 5  # Depth of the arrowhead
        for x_offset in range(arrowhead_depth):
            # Calculate the width of the arrowhead at this level
            arrowhead_width = arrowhead_depth - x_offset
            for y_offset in range(height // 2 - x_offset, height // 2 + x_offset + 1):
                # Draw the arrowhead at the tip of the shaft (right end)
                matrix.pixel((start_x + arrow_height - arrowhead_depth + x_offset - 8, y_offset), (255, 0, 0))

        matrix.show()
        matrix.delay(50)
    print("Exiting caution effect.")

def effect_clear():
    """Clear the matrix."""
    global stop_event
    if get_current_effect() == 'clear':
         # Clear the matrix first
        matrix.reset()
        arrow_height = 10  # Adjusted for a larger arrow
        width, height = 16, 16
        start_y = 5
        for y_offset in range(arrow_height):
            # Calculate the current y position of this part of the arrow
            current_y = start_y + y_offset
            
            if current_y < 0 or current_y >= height:
                continue  # Skip drawing outside the matrix bounds
            
            # Larger Arrow shaft
            if y_offset > 0:  # Skip the top 3 rows for the arrowhead
                for x_offset in range(width // 2 - 1, width // 2 + 2):  # Widen the shaft
                    matrix.pixel((x_offset, current_y), (0, 128, 0))
            
            # Arrowhead
            arrowhead_depth = 5  # Depth of the arrowhead
            for y_offset in range(arrowhead_depth):
                # Draw the arrowhead for every y_offset without skipping
                # Calculate the width of the arrowhead at this level
                arrowhead_width = arrowhead_depth - y_offset
                for x_offset in range(width // 2 - y_offset, width // 2 + y_offset + 1):
                    # Adjust y position to start drawing from the top of the arrowhead
                    current_y_position = start_y - arrowhead_depth + y_offset + 1
                    matrix.pixel((x_offset, current_y_position), (0, 128, 0))

        # Display the updated matrix
        matrix.show()

def effect_clearAnimation():
    """Display an upward-scrolling, larger arrow with a sharp point."""
    arrow_height = 10  # Adjusted for a larger arrow
    width, height = 16, 16
    scroll_speed = 50  # Milliseconds between updates

    while not stop_event.is_set() and get_current_effect() == 'clearAnimation':
        for start_y in range(height, -arrow_height, -1):
            matrix.reset()  # Clear the matrix

            # Draw the larger arrow pointing up
            for y_offset in range(arrow_height):
                # Calculate the current y position of this part of the arrow
                current_y = start_y + y_offset
                
                if current_y < 0 or current_y >= height:
                    continue  # Skip drawing outside the matrix bounds
                
                # Larger Arrow shaft
                if y_offset > 0:  # Skip the top 3 rows for the arrowhead
                    for x_offset in range(width // 2 - 1, width // 2 + 2):  # Widen the shaft
                        matrix.pixel((x_offset, current_y), (0, 128, 0))
                
                # Arrowhead
                arrowhead_depth = 5  # Depth of the arrowhead
                for y_offset in range(arrowhead_depth):
                    # Draw the arrowhead for every y_offset without skipping
                    # Calculate the width of the arrowhead at this level
                    arrowhead_width = arrowhead_depth - y_offset
                    for x_offset in range(width // 2 - y_offset, width // 2 + y_offset + 1):
                        # Adjust y position to start drawing from the top of the arrowhead
                        current_y_position = start_y - arrowhead_depth + y_offset + 1
                        matrix.pixel((x_offset, current_y_position), (0, 128, 0))


            matrix.show()
            matrix.delay(scroll_speed)



def effect_medical():
    """Flash red and white for medical."""
    while not stop_event.is_set() and get_current_effect() == 'medical':
        # Define the size of the matrix and cross thickness
        width = 16
        height = 16
        cross_thickness = max(1, min(width, height) // 8)  # Adjust the thickness as needed

        # First, set the entire matrix to white for the background
        matrix.reset(matrix.color('white'))

        # Calculate the starting and ending points for the vertical part of the cross
        vertical_start = height // 2 - cross_thickness // 2
        vertical_end = vertical_start + cross_thickness
        # Draw the vertical part of the cross in red
        for y in range(vertical_start, vertical_end):
            for x in range(width):
                matrix.pixel((x, y), (255, 0, 0))

        # Calculate the starting and ending points for the horizontal part of the cross
        horizontal_start = width // 2 - cross_thickness // 2
        horizontal_end = horizontal_start + cross_thickness
        # Draw the horizontal part of the cross in red
        for x in range(horizontal_start, horizontal_end):
            for y in range(height):
                matrix.pixel((x, y), (255, 0, 0))

        matrix.show()
        matrix.delay(500)

        # Optional: Flash the cross by toggling between the cross and a blank state
        # Define the size of the matrix and cross thickness
        width = 16
        height = 16
        cross_thickness = max(1, min(width, height) // 8)  # Adjust the thickness as needed

        # First, set the entire matrix to white for the background
        matrix.reset(matrix.color('red'))

        # Calculate the starting and ending points for the vertical part of the cross
        vertical_start = height // 2 - cross_thickness // 2
        vertical_end = vertical_start + cross_thickness
        # Draw the vertical part of the cross in red
        for y in range(vertical_start, vertical_end):
            for x in range(width):
                matrix.pixel((x, y), (255, 255, 255))

        # Calculate the starting and ending points for the horizontal part of the cross
        horizontal_start = width // 2 - cross_thickness // 2
        horizontal_end = horizontal_start + cross_thickness
        # Draw the horizontal part of the cross in red
        for x in range(horizontal_start, horizontal_end):
            for y in range(height):
                matrix.pixel((x, y), (255, 255, 255))

        matrix.show()
        matrix.delay(500)

    print("Exiting medical effect.")

def effect_lastLap():
    """Display white for the last lap."""
    if get_current_effect() == 'lastLap':
        matrix.reset(matrix.color('white'))
        matrix.show()

def effect_off():
    """Display off."""
    if get_current_effect() == 'off':
        matrix.reset()
        matrix.show()

def effect_lastLapAnimation():
    """Display white for the last lap."""
    while not stop_event.is_set() and get_current_effect() == 'lastLapAnimation':
        # Define the checkerboard pattern size
        checker_size = 2  # Size of each checker square
        width, height = 16, 16

        matrix.reset(matrix.color('white'))
         # Loop through each cell in the matrix to create the checkerboard pattern
        for y in range(height):
            for x in range(width):
                # Determine if the current cell should be black or remain white
                if (x // checker_size % 2 == 0) ^ (y // checker_size % 2 == 0):
                    matrix.pixel((x, y), (0, 0, 0))  # Set to black

        # Display the checkerboard pattern
        matrix.show()
        matrix.delay(1000)
        # Clear the matrix first
        matrix.reset()

        # Loop through each cell in the matrix to create the checkerboard pattern
        for y in range(height):
            for x in range(width):
                # Determine if the current cell should be white or remain black
                if (x // checker_size % 2 == 0) ^ (y // checker_size % 2 == 0):
                    matrix.pixel((x, y), (255, 255, 255))  # Set to white

        # Display the checkerboard pattern
        matrix.show()

        # Keep the pattern displayed for a while before checking if the effect should stop
        matrix.delay(1000)

# Adjust the code to make sure the rider's name and time are placed closer together
def _xy_to_index(x, y):
    """
    Map virtual (x,y) to linear LED index for a grid of WS2812 16x16 panels,
    chained left-to-right then next row (row-major).
    Adjust SERPENTINE_PER_ROW and PANEL_CHAIN_ORDER to your physical order.
    """
    # Which panel tile
    tile_x = x // PANEL_W
    tile_y = y // PANEL_H

    # Local coords within a panel
    lx = x % PANEL_W
    ly = y % PANEL_H

    # Index of panel in the chain (panel_number)
    if PANEL_CHAIN_ORDER == 'row-major':
        panel_idx = tile_y * PANELS_X + tile_x
    else:  # 'col-major'
        panel_idx = tile_x * PANELS_Y + tile_y

    # Within each 16x16 panel, many are serpentine by row
    if SERPENTINE_PER_ROW and (ly % 2 == 1):
        # odd row: reversed
        li = ly * PANEL_W + (PANEL_W - 1 - lx)
    else:
        li = ly * PANEL_W + lx

    # Global index = panel offset + local index
    leds_per_panel = PANEL_W * PANEL_H
    return panel_idx * leds_per_panel + li

def _put_pixel(matrix, x, y, color):
    """Write a pixel using either (x,y) API or linear-index API."""
    if hasattr(matrix, 'pixel'):
        matrix.pixel((x, y), color)
    elif hasattr(matrix, 'set_pixel'):
        idx = _xy_to_index(x, y)
        matrix.set_pixel(idx, color)
    else:
        # Fallback: assume linear is required
        idx = _xy_to_index(x, y)
        matrix[idx] = color  # e.g., neopixel-like

# ====== MAIN EFFECT with optional diagnostics ======
# Trigger diagnostics by calling: effect_times(rider_data="__TEST__") OR effect_times(rider_data, test_mode=True)
def effect_times(rider_data, test_mode=False):
    """
    Normal: current/previous rider on a 32x32 (2x2) WS2812 wall.
    Diagnostics: when test_mode=True or rider_data == "__TEST__", run panel tests, then resume normal.
    """
    # ---- DIAGNOSTIC MODE ----
    if test_mode or rider_data == "__TEST__":
        try:
            print("[times] DIAGNOSTIC: Test 1 (fill white)")
            # Fill all white
            for y in range(PANEL_H * PANELS_Y):
                for x in range(PANEL_W * PANELS_X):
                    _put_pixel(matrix, x, y, (60, 60, 60))
            matrix.show()
            matrix.delay(600)

            print("[times] DIAGNOSTIC: Test 2 (per-panel colors)")
            panel_colors = [(80,0,0), (0,80,0), (0,0,80), (60,60,0)]
            for k, (tx, ty) in enumerate(PANEL_ORDER):
                _clear_matrix(matrix)
                # paint panel k only
                for ly in range(PANEL_H):
                    for lx in range(PANEL_W):
                        x = tx * PANEL_W + lx
                        y = ty * PANEL_H + ly
                        _put_pixel(matrix, x, y, panel_colors[k])
                matrix.show()
                print(f"  Panel {k} lit at tile ({tx},{ty})")
                matrix.delay(600)

            print("[times] DIAGNOSTIC: Test 3 (32x32 corners)")
            _clear_matrix(matrix)
            for (x, y) in [(0,0), (31,0), (0,31), (31,31)]:
                _put_pixel(matrix, x, y, (120, 120, 120))
            matrix.show()
            matrix.delay(800)

            print("[times] DIAGNOSTIC: Test 4 (horizontal scan 32x32)")
            _clear_matrix(matrix)
            for y in range(32):
                for x in range(32):
                    _put_pixel(matrix, x, y, (80, 80, 80))
                    if x > 0:
                        _put_pixel(matrix, x-1, y, (0, 0, 0))
                    matrix.show()
                    matrix.delay(5)  # ~5 ms per step
            matrix.delay(200)

            print("[times] DIAGNOSTIC: Test 5 (vertical scan 32x32)")
            _clear_matrix(matrix)
            for x in range(32):
                for y in range(32):
                    _put_pixel(matrix, x, y, (80, 0, 80))
                    if y > 0:
                        _put_pixel(matrix, x, y-1, (0, 0, 0))
                    matrix.show()
                    matrix.delay(5)
            _clear_matrix(matrix)
            matrix.show()
            print("[times] DIAGNOSTIC complete → resuming normal effect.")
            # fall through to normal rendering afterward
        except Exception as e:
            print(f"[times] DIAGNOSTIC error: {e}")

    # ---- NORMAL RENDER (current/previous) ----
    history = deque(maxlen=2)

    def parse_triplet(payload: str):
        parts = payload.split("-")
        if len(parts) != 3:
            raise ValueError(f"Invalid rider data format: {payload!r}")
        return parts[0].strip(), parts[1].strip(), parts[2].strip()

    width, height = 32, 32  # 2x2 of 16x16

    while not stop_event.is_set() and get_current_effect() == "times":
        # Ingest new payload (avoid dup so "previous" stays meaningful)
        if isinstance(rider_data, str) and rider_data and rider_data != "__TEST__":
            try:
                t = parse_triplet(rider_data)
                if not history or history[-1] != t:
                    history.append(t)
            except Exception as e:
                print(f"[times] invalid payload {rider_data!r}: {e}")

        if not history:
            # show nothing but keep loop alive
            _clear_matrix(matrix)
            matrix.show()
            matrix.delay(120)
            continue

        current = history[-1]
        previous = history[-2] if len(history) >= 2 else history[-1]

        # Offscreen render
        img = Image.new("RGB", (width, height), (0, 0, 0))
        d   = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        try:
            bbox = font.getbbox("Hg")
            LINE_H = bbox[3] - bbox[1]
        except Exception:
            LINE_H = 8
        LINE_GAP = 0  # exactly zero

        def draw_block(x, y, triplet, dim=False):
            bike, name, lap = triplet
            name_color = get_bike_color(bike)
            time_color = (180, 180, 180) if dim else (255, 255, 255)
            d.text((x, y), name, font=font, fill=name_color)
            d.text((x, y + LINE_H + LINE_GAP), lap, font=font, fill=time_color)

        # current on top half (0..15), previous on bottom half (16..31)
        draw_block(0, 0,   current,  dim=False)
        draw_block(0, 16,  previous, dim=True)

        # Push to LEDs
        for y in range(height):
            for x in range(width):
                _put_pixel(matrix, x, y, img.getpixel((x, y)))

        matrix.show()
        matrix.delay(FLASH_DELAY)



# Helper function to return a color for each bike
def get_bike_color(bike_name):
    """Return a color based on bike brand."""
    bike_colors = {
        'beta': (135, 206, 250),    # Light Blue for Beta (Sky Blue)
        'gasgas': (255, 0, 0),      # Red for GasGas
        'honda': (255, 0, 0),       # Red for Honda
        'husqvarna': (255, 255, 255),  # White for Husqvarna
        'ktm': (255, 140, 0),       # Orange for KTM
        'kawasaki': (0, 255, 0),    # Green for Kawasaki
        'stark': (255, 0, 0),       # Red for Stark
        'suzuki': (255, 255, 0),    # Yellow for Suzuki
        'yamaha': (0, 0, 255)       # Blue for Yamaha
    }

    
    # Default to white if no match
    return bike_colors.get(bike_name.lower(), (255, 255, 255))



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
    'startGateCountdown': effect_startGateCountdown,
}

def apply_effect(effect_name, rider_data=None):
    global stop_event, current_effect_thread
    if current_effect_thread is not None:
        stop_event.set()  # Signal the current effect to stop
        current_effect_thread.join()  # Wait for the current effect to acknowledge and stop
        stop_event.clear()  # Reset for the next effect

    set_current_effect(effect_name)  # Update the current effect
    current_effect_thread = threading.Thread(target=effects[effect_name], args=(rider_data,))
    current_effect_thread.start()

def listen_for_commands():
    """Continuously listen for new commands and apply effects accordingly."""
    while True:
        input_data = sys.stdin.readline().strip()
        
        if not input_data:
            continue
        
        try:
            # Parse the incoming data
            data = json.loads(input_data)

            effect_name = data.get('effect', None)
            rider_data = data.get('riderData', None)

            if effect_name and effect_name in effects:
                apply_effect(effect_name, rider_data)
            else:
                print(f"Unknown effect: {effect_name}")
        except json.JSONDecodeError:
            print("Invalid data received. Skipping...")
        
if __name__ == "__main__":
    listen_for_commands()
