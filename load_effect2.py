import sys
import json
import threading
from src.led_matrix import Matrix, pixel_height, pixel_width
from PIL import Image, ImageDraw, ImageFont
from collections import deque
# Optional override: 'auto' | 'wide16x64' | 'tall32x32'
FORCE_LAYOUT = 'wide16x64'   # set to 'wide16x64' if you want to force side-by-side

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
def effect_times(rider_data):
    """
    Shows the most recent rider and lap, plus the previous one.
    - If matrix is 16x64 (wide): current = left 32x16, previous = right 32x16.
    - If matrix is 32x32 (tall): current = top 16px (2 lines), previous = bottom 16px (2 lines).
    Vertical spacing between name and time is exactly 0 pixels.
    """
    history = deque(maxlen=2)  # [older, newer]; we append on the right

    def parse_triplet(payload: str):
        parts = payload.split('-')
        if len(parts) != 3:
            raise ValueError(f"Invalid rider data format: {payload!r}")
        return parts[0].strip(), parts[1].strip(), parts[2].strip()  # (bike, name, lap)

    # Best-effort to get matrix dims if your driver exposes them; else fall back.
    try:
        width = getattr(matrix, 'width', None) or 64
        height = getattr(matrix, 'height', None) or 16
    except Exception:
        width, height = 64, 16

    def pick_layout(w, h):
        if FORCE_LAYOUT == 'wide16x64':
            return 'wide'
        if FORCE_LAYOUT == 'tall32x32':
            return 'tall'
        # Auto-detect
        if h == 16 and w >= 64:
            return 'wide'
        if w == 32 and h >= 32:
            return 'tall'
        # Fallback: prefer wide if it's a single 16-pixel-tall strip
        return 'wide' if h <= 16 else 'tall'

    layout = pick_layout(width, height)

    while not stop_event.is_set() and get_current_effect() == 'times':
        matrix.reset(matrix.color('black'))

        # Ingest new data if present
        if isinstance(rider_data, str) and rider_data:
            try:
                triplet = parse_triplet(rider_data)
                if not history or history[-1] != triplet:
                    history.append(triplet)
            except Exception as e:
                print(f"[times] Ignoring invalid rider_data={rider_data!r}: {e}")

        if not history:
            print("[times] No rider data; skipping frame.")
            matrix.delay(200)
            continue

        # Current = most recent; Previous = second most recent or fallback to current.
        current = history[-1]
        previous = history[-2] if len(history) >= 2 else current

        # Build offscreen image for the full canvas we think we have
        from PIL import Image, ImageDraw, ImageFont
        image = Image.new("RGB", (width, height), (0, 0, 0))
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()

        # Measure font line height; place time immediately below name (no extra gap)
        try:
            bbox = font.getbbox("Hg")
            LINE_H = bbox[3] - bbox[1]
        except Exception:
            LINE_H = 8  # default font height ~8px
        LINE_GAP = 0  # <- exactly zero as requested

        def draw_block(x, y, triplet, dim=False):
            bike, name, lap = triplet
            name_color = get_bike_color(bike)
            time_color = (180, 180, 180) if dim else (255, 255, 255)
            # Name
            draw.text((x, y), name, font=font, fill=name_color)
            # Time immediately below name; no extra spacing
            draw.text((x, y + LINE_H + LINE_GAP), lap, font=font, fill=time_color)

        if layout == 'wide':
            # Full canvas assumed 16 high, 64 wide (or similar wide strip)
            # Left pane 0..31: current; Right pane 32..63: previous
            pane_w = width // 2  # expect 32
            # Clamp to avoid text spilling if non-64 widths
            pane_w = max(16, min(pane_w, 64))
            left_x, right_x = 0, pane_w
            top_y = 0  # 16-px tall
            draw_block(left_x, 0, current, dim=False)
            draw_block(right_x, 0, previous, dim=True)
        else:
            # Tall 32x32: current top half (0..15), previous bottom half (16..31)
            draw_block(0, 0, current, dim=False)
            draw_block(0, 16, previous, dim=True)

        # Push pixels to the matrix
        for x in range(width):
            for y in range(height):
                matrix.pixel((x, y), image.getpixel((x, y)))

        matrix.delay(200)
        matrix.show()
        matrix.delay(FLASH_DELAY)
        
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
