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
    print("Exiting caution effect.")

def effect_caution_right():
    """Red, yellow, repeat."""
    while not stop_event.is_set() and get_current_effect() == 'cautionRight':
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
        for x_offset in range(arrowhead_depth):
            # Calculate the width of the arrowhead at this level
            arrowhead_width = arrowhead_depth - x_offset
            # for y_offset in range(height // 2 - x_offset, height // 2 + x_offset + 1):
            for y_offset in range(height // 2 - x_offset + 3, height // 2 + x_offset -2):
                print("y offset",y_offset)
                # Draw the arrowhead at the tip of the shaft (right end)
                matrix.pixel((start_x + arrow_height - arrowhead_depth + x_offset, y_offset), (255, 0, 0))

        matrix.show()
        # matrix.delay(50)
        # matrix.reset(matrix.color('red'))
        
        # # Draw the arrow shaft (horizontal now)
        # for x_offset in range(arrow_height):
        #     current_x = start_x + x_offset
            
        #     if current_x < 0 or current_x >= width:
        #         continue  # Skip drawing outside the matrix bounds

        #     # Shaft width
        #     if x_offset > 0:  # Skip the first few rows for the arrowhead
        #         for y_offset in range(height // 2 - 1, height // 2 + 2):  # Widen the shaft vertically
        #             matrix.pixel((current_x, y_offset), (255, 0, 0))  # Red color for the arrow shaft

        # for x_offset in range(arrowhead_depth):
        #     # Calculate the width of the arrowhead at this level
        #     arrowhead_width = arrowhead_depth - x_offset
        #     for y_offset in range(height // 2 - x_offset, height // 2 + x_offset + 1):
        #         # Draw the arrowhead at the tip of the shaft (right end)
        #         matrix.pixel((start_x + arrow_height - arrowhead_depth + x_offset, y_offset), (255, 140, 0))

        # matrix.show()
        # matrix.delay(50)
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
