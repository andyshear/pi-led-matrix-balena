import sys
import json
import threading
from src.led_matrix import Matrix, pixel_height, pixel_width
from PIL import Image, ImageDraw, ImageFont

# Initialize global variables for effect control
current_effect = None
effect_change_lock = threading.Lock()
matrix = Matrix()  # Initialize your matrix here
stop_event = threading.Event()  # Define the stop event here
current_effect_thread = None  # Keep a reference to the current effect thread

# Define the delay for flashing and scrolling
FLASH_DELAY = 200  # milliseconds for color change
SCROLL_DELAY = 20  # milliseconds for scroll speed
MESSAGE = "CAUTION"
FONT_SIZE = 16  # Adjust as needed
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
            # Draw from top-right to bottom-left
            matrix.pixel((width - 1 - i, i), (255, 0, 0))

        matrix.show()
        matrix.delay(50)
        matrix.reset()
        matrix.show()
        matrix.delay(50)
        # matrix.reset()
        # matrix.show()
        # matrix.delay(50)
        # matrix.reset(matrix.color('yellow'))
        # matrix.show()
        # matrix.delay(50)
    print("Exiting caution effect.")

def effect_clear():
    """Clear the matrix."""
    global stop_event
    if get_current_effect() == 'clear':
         # Clear the matrix first
        matrix.reset()

        # Coordinates for a simple thumbs-up
        # Adjust these based on your matrix size
        checkmark_pixels = [
            (5, 10), (5, 11), (6, 10), (6, 11),  # Lower left part
            (7, 9), (7, 8), (8, 9), (8, 8),      # Middle part, moving up and to the right
            (9, 7), (9, 6), (10, 7), (10, 6),    # Continuation of middle part
            (11, 5), (11, 4), (12, 5), (12, 4),  # Top of the middle part, before the diagonal
            (9, 5), (9, 4), (10, 5), (10, 4),    # Starting the diagonal downwards
            (7, 7), (7, 6), (8, 7), (8, 6),      # Middle of the diagonal downwards
            (5, 9), (5, 8), (6, 9), (6, 8),      # End of the diagonal, close to the starting point
        ]
        # Loop through each coordinate and light it up
        for x, y in checkmark_pixels:
            matrix.pixel((x, y), (0, 128, 0))  # White color for thumbs-up

        # Display the updated matrix
        matrix.show()

def effect_clearanimation():
    """Display an upward-scrolling arrow."""
    arrow_height = 5  # Adjust based on your matrix size
    width, height = config['pixel_width'], config['pixel_height']
    scroll_speed = 200  # Milliseconds between updates

    while not stop_event.is_set() and get_current_effect() == 'clearanimation':
        for start_y in range(height + arrow_height, -arrow_height, -1):
            matrix.reset(matrix.color('green'))  # Clear the matrix

            # Draw the arrow
            for y_offset in range(arrow_height):
                if start_y - y_offset < 0 or start_y - y_offset >= height:
                    continue  # Skip drawing outside the matrix bounds
                
                # Arrow shaft
                matrix.pixel((width // 2, start_y - y_offset), (255, 255, 255))
                
                # Arrowhead
                if y_offset == 0:
                    matrix.pixel((width // 2 - 1, start_y), (255, 255, 255))
                    matrix.pixel((width // 2 + 1, start_y), (255, 255, 255))
                    matrix.pixel((width // 2, start_y + 1), (255, 255, 255))
            
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
        matrix.reset()  # Clear the matrix
        matrix.show()
        matrix.delay(500)

    print("Exiting medical effect.")

def effect_lastLap():
    """Display white for the last lap."""
    if get_current_effect() == 'lastLap':
        matrix.reset(matrix.color('white'))
        matrix.show()

effects = {
    'caution': effect_caution,
    'clear': effect_clear,
    'clearAnimation': effect_clearanimation,
    'medical': effect_medical,
    'lastLap': effect_lastLap,
}

def apply_effect(effect_name):
    global stop_event, current_effect_thread
    if current_effect_thread is not None:
        stop_event.set()  # Signal the current effect to stop
        current_effect_thread.join()  # Wait for the current effect to acknowledge and stop
        stop_event.clear()  # Reset for the next effect

    set_current_effect(effect_name)  # Update the current effect
    current_effect_thread = threading.Thread(target=effects[effect_name])
    current_effect_thread.start()

def listen_for_commands():
    """Continuously listen for new commands and apply effects accordingly."""
    while True:
        new_effect = input("Enter new effect (caution, clear, clearAnimation, medical, lastLap) or 'exit' to quit: ")
        if new_effect == 'exit':
            if current_effect_thread is not None:
                stop_event.set()
                current_effect_thread.join()
            break
        if new_effect in effects:
            apply_effect(new_effect)
        else:
            print(f"Unknown effect: {new_effect}")

if __name__ == "__main__":
    initial_effect = sys.argv[1] if len(sys.argv) > 1 else None
    if initial_effect:
        apply_effect(initial_effect)
    listen_for_commands()
