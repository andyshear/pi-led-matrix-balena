import sys
import json
import threading
from src.led_matrix import Matrix, pixel_height, pixel_width
from PIL import Image, ImageDraw, ImageFont
from collections import deque
import queue

times_history = deque(maxlen=2)     # [(bike, name, time)]
times_queue = queue.Queue()         # push rider payloads here

laps_by_rider = {}                  # rider_name -> lap count
_last_time_by_rider = {}            # rider_name -> last seen time (to avoid double-increment)

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
def effect_times(_initial_rider_data_ignored):
    """
    64x16 layout: left 32x16 = current, right 32x16 = previous.
    Top line (NAME L{laps}) scrolls horizontally; bottom line (lap time) is static.
    Payload: bike-rider-laps-lapTime
    """
    # ---- helpers ----
    def parse_quad(payload: str):
        parts = [p.strip() for p in payload.split('-')]
        if len(parts) != 4:
            raise ValueError(f"Invalid rider data format: {payload!r} (expected 4 fields)")
        bike, name, laps_str, lap_time = parts
        return bike, name, laps_str, lap_time

    def record_seen(name: str, lap_time: str, laps_str: str):
        try:
            laps_val = int(str(laps_str))
        except Exception:
            laps_val = laps_by_rider.get(name, 0)
        laps_by_rider[name] = laps_val
        _last_time_by_rider[name] = lap_time

    width, height = 64, 16
    pane_w = 32

    font = ImageFont.load_default()
    line_h = 8
    LINE_GAP = 0
    y0 = -2
    y1 = y0 + line_h + LINE_GAP

    # per-pane scroll state (top line only)
    cur_scroll = 0
    prev_scroll = 0
    SCROLL_PX_PER_FRAME = 2   # a tad faster; tweak if needed
    IDLE_SLEEP_MS = 20

    # caches: split into top (scrolling) and bottom (static) per pane
    cur_key = prev_key = None
    cur_top_surface = cur_bot_surface = None
    prev_top_surface = prev_bot_surface = None
    cur_top_w = prev_top_w = pane_w

    def make_surfaces(entry, dim: bool):
        """
        entry = (bike, name, laps_str, lap_time)
        Returns:
         - top_surface (W_top x 16) with ONLY the top line drawn (can be wider than pane)
         - top_w (its width)
         - bot_surface (pane_w x 16) with ONLY the bottom line drawn (fixed width)
        """
        bike, name, laps_str, lap_time = entry
        try:
            laps_val = int(laps_str)
        except Exception:
            laps_val = laps_by_rider.get(name, 0)

        top_text = f"{name} L{laps_val}"
        name_color = get_bike_color(bike)
        time_color = (180, 180, 180) if dim else (255, 255, 255)

        # measure widths
        tmp = Image.new("RGB", (1, 1))
        dd = ImageDraw.Draw(tmp)
        w_top = dd.textbbox((0, 0), top_text, font=font)[2]
        top_w = max(pane_w, w_top) + 2  # top can scroll beyond pane

        # build top (scrolling) surface
        top_surface = Image.new("RGB", (top_w, height), (0, 0, 0))
        d_top = ImageDraw.Draw(top_surface)
        d_top.text((0, y0), top_text, font=font, fill=name_color)

        # build bottom (static) surface exactly pane_w wide
        bot_surface = Image.new("RGB", (pane_w, height), (0, 0, 0))
        d_bot = ImageDraw.Draw(bot_surface)
        d_bot.text((-1, y1), lap_time, font=font, fill=time_color)

        return top_surface, top_w, bot_surface

    while not stop_event.is_set() and get_current_effect() == 'times':
        # drain queue
        while True:
            try:
                payload = times_queue.get_nowait()
            except queue.Empty:
                break
            try:
                quad = parse_quad(payload)
                record_seen(quad[1], quad[3], quad[2])
                if not times_history or times_history[-1] != quad:
                    times_history.append(quad)
            except Exception as e:
                print(f"[times] Skip invalid rider_data={payload!r}: {e}")

        if not times_history:
            matrix.reset(matrix.color('black')); matrix.show(); matrix.delay(60)
            continue

        current  = times_history[-1]
        previous = times_history[-2] if len(times_history) >= 2 else current

        # keys include normalized laps + lap_time so we rebuild when they change
        cur_laps  = laps_by_rider.get(current[1],  current[2])
        prev_laps = laps_by_rider.get(previous[1], previous[2])
        this_cur_key  = ('cur',  current[0],  current[1],  str(cur_laps),  current[3])
        this_prev_key = ('prev', previous[0], previous[1], str(prev_laps), previous[3])

        if this_cur_key != cur_key:
            cur_entry = (current[0], current[1], str(cur_laps), current[3])
            cur_top_surface, cur_top_w, cur_bot_surface = make_surfaces(cur_entry, dim=False)
            cur_key = this_cur_key
            cur_scroll = 0 if cur_top_w <= pane_w else cur_scroll % cur_top_w

        if this_prev_key != prev_key:
            prev_entry = (previous[0], previous[1], str(p_

        
def effect_startGateCountdown():
    """Display '30', then '5', then flash green 3 times, then turn off."""
    from PIL import Image, ImageDraw, ImageFont

    width, height = 32, 16  # Match your matrix
    font = ImageFont.load_default()

    def render_text_frame(text, color):
        image = Image.new("RGB", (width, height), (0, 0, 0))
        draw = ImageDraw.Draw(image)

        y_offset = 0
        draw.text((0, y_offset), text, font=font, fill=color)

        for x in range(width):
            for y in range(height):
                pixel_color = image.getpixel((x, y))
                matrix.pixel((x, y), pixel_color)

        matrix.show()

    if stop_event.is_set():
        return

    # Step 1: Show "30"
    print("Start Gate Countdown: Showing 30")
    matrix.reset(matrix.color('black'))
    render_text_frame("30", (255, 255, 255))  # White text
    matrix.delay(25000)

    if stop_event.is_set() or get_current_effect() != 'startGateCountdown':
        return

    # Step 2: Show "5"
    print("Start Gate Countdown: Showing 5")
    matrix.reset(matrix.color('black'))
    render_text_frame("5", (255, 0, 0))  # Red text
    matrix.delay(5000)

    if stop_event.is_set() or get_current_effect() != 'startGateCountdown':
        return

    # Step 3: Flash green 3 times
    print("Start Gate Countdown: Flashing green")
    for _ in range(3):
        matrix.fill((0, 255, 0))  # Bright green
        matrix.show()
        matrix.delay(300)
        matrix.fill((0, 0, 0))  # Off
        matrix.show()
        matrix.delay(300)

    matrix.fill((0, 0, 0))  # Clear at end
    matrix.show()



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
    # If the times effect is already running, just enqueue new data and don't restart
    if effect_name == 'times' and get_current_effect() == 'times' and current_effect_thread is not None and current_effect_thread.is_alive():
        if isinstance(rider_data, str) and rider_data:
            times_queue.put(rider_data)
        return

    # switching effects or starting fresh
    if current_effect_thread is not None:
        stop_event.set()
        current_effect_thread.join()
        stop_event.clear()

    set_current_effect(effect_name)
    current_effect_thread = threading.Thread(target=effects[effect_name], args=(rider_data,))
    current_effect_thread.start()

    # if launching times with an initial payload, enqueue it
    if effect_name == 'times' and isinstance(rider_data, str) and rider_data:
        times_queue.put(rider_data)

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
