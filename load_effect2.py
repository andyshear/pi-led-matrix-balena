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

def effect_times(_initial_rider_data_ignored):
    """
    128x16 layout with 4 horizontal lanes (each 32x16):
      Lane 0 | Lane 1 | Lane 2 | Lane 3

    - First time a rider is seen, they are assigned to the next lane in sequence
      (0→1→2→3→0…) and remain sticky there.
    - On update, that rider is shown immediately in their lane.
    - Each lane cycles through its roster forever on a fixed interval.
    - No marquee; rider number and time are static positions inside the pane.

    Payload from Node: "bike-#RIDERNUM-laps-lapTime"
    """
    import time

    # ----- helpers -----
    def parse_quad(payload: str):
        parts = [p.strip() for p in payload.split('-')]
        if len(parts) != 4:
            raise ValueError(f"Invalid rider data format: {payload!r} (expected 4 fields)")
        return parts[0], parts[1], parts[2], parts[3]  # bike, name, laps_str, lap_time

    def record_seen(name: str, lap_time: str, laps_str: str):
        try:
            laps_val = int(str(laps_str))
        except Exception:
            laps_val = laps_by_rider.get(name, 0)
        laps_by_rider[name] = laps_val
        _last_time_by_rider[name] = lap_time

    # ----- geometry -----
    WIDTH, HEIGHT = pixel_width, pixel_height  # 128x16 from your config
    NUM_LANES = 4
    PANE_W = WIDTH // NUM_LANES  # 32
    PANE_H = HEIGHT              # 16

    font = ImageFont.load_default()
    line_h = 8

    # vertical placement (lift everything by -2px to remove the gap you saw)
    Y_OFFSET = -2
    NAME_Y = Y_OFFSET            # top line: rider number (fixed)
    TIME_Y = NAME_Y + line_h     # bottom line: lap time (fixed)

    # ----- cycling & speed knobs -----
    IDLE_SLEEP_MS = 20
    ROTATE_INTERVAL_MS = 900  # per-lane rotation cadence

    # ----- lane bookkeeping -----
    rider_lane = {}                       # name -> lane idx
    next_lane_toggle = 0                  # 0..3 round-robin
    lane_roster = [[] for _ in range(NUM_LANES)]
    lane_active_idx = [0 for _ in range(NUM_LANES)]
    lane_next_rotate_at = [0 for _ in range(NUM_LANES)]

    # latest record per rider
    rider_rec = {}  # name -> (bike, name, laps_str, lap_time)

    def assign_lane_if_new(name: str):
        nonlocal next_lane_toggle
        if name in rider_lane:
            return rider_lane[name]
        lane = next_lane_toggle
        next_lane_toggle = (next_lane_toggle + 1) % NUM_LANES
        rider_lane[name] = lane
        if name not in lane_roster[lane]:
            lane_roster[lane].append(name)
        return lane

    def set_active_to(name: str, lane: int):
        """Show this rider immediately in their lane and hold until next interval."""
        try:
            idx = lane_roster[lane].index(name)
        except ValueError:
            lane_roster[lane].append(name)
            idx = len(lane_roster[lane]) - 1
        lane_active_idx[lane] = idx
        lane_next_rotate_at[lane] = int(time.time() * 1000) + ROTATE_INTERVAL_MS

    while not stop_event.is_set() and get_current_effect() == 'times':
        now_ms = int(time.time() * 1000)

        # ---- drain queue (non-blocking) ----
        while True:
            try:
                payload = times_queue.get_nowait()
            except queue.Empty:
                break
            try:
                bike, name, laps_str, lap_time = parse_quad(payload)
                record_seen(name, lap_time, laps_str)
                rider_rec[name] = (bike, name, laps_str, lap_time)
                lane = assign_lane_if_new(name)
                if name not in lane_roster[lane]:
                    lane_roster[lane].append(name)
                set_active_to(name, lane)  # instant show on update
            except Exception as e:
                print(f"[times] Skip invalid rider_data={payload!r}: {e}")

        # ---- rotate lanes on interval ----
        for lane in range(NUM_LANES):
            if not lane_roster[lane]:
                continue
            if now_ms >= lane_next_rotate_at[lane]:
                lane_active_idx[lane] = (lane_active_idx[lane] + 1) % len(lane_roster[lane])
                lane_next_rotate_at[lane] = now_ms + ROTATE_INTERVAL_MS

        # ---- compose frame (single PIL frame, then blit to matrix) ----
        frame = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
        draw = ImageDraw.Draw(frame)

        for lane in range(NUM_LANES):
            if not lane_roster[lane]:
                continue

            pane_x0 = lane * PANE_W  # left edge of this lane
            active_name = lane_roster[lane][lane_active_idx[lane]]

            # pull data
            bike, nm, _laps_str, lap_time = rider_rec.get(active_name, ("", active_name, "", ""))

            # choose colors (brand for number, white for time)
            num_color = get_bike_color(bike)
            time_color = (255, 255, 255)

            # draw number (top) and time (bottom), fixed positions
            draw.text((pane_x0, NAME_Y), nm, font=font, fill=num_color)
            draw.text((pane_x0, TIME_Y), lap_time, font=font, fill=time_color)

        # ---- push pixels ----
        for x in range(WIDTH):
            for y in range(HEIGHT):
                matrix.pixel((x, y), frame.getpixel((x, y)))
        matrix.show()
        matrix.delay(IDLE_SLEEP_MS)



        
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
        'yamaha': (80, 160, 255)   # Lighter, brighter Yamaha blue
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
