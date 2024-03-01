import sys
import json
import threading
from src.led_matrix import Matrix, pixel_height, pixel_width
from PIL import Image

# Initialize global variables for effect control
current_effect = None
effect_change_lock = threading.Lock()
matrix = Matrix()  # Initialize your matrix here
stop_event = threading.Event()  # Define the stop event here
current_effect_thread = None  # Keep a reference to the current effect thread

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
        matrix.reset(matrix.color('red'))
        matrix.show()
        matrix.delay(200)
        matrix.reset(matrix.color('yellow'))
        matrix.show()
        matrix.delay(200)
    print("Exiting caution effect.")

def effect_clear():
    """Clear the matrix."""
    global stop_event
    if get_current_effect() == 'clear':
        matrix.reset(matrix.color('green'))
        matrix.show()

def effect_medical():
    """Flash red and white for medical."""
    while not stop_event.is_set() and get_current_effect() == 'medical':
        matrix.reset(matrix.color('red'))
        matrix.show()
        matrix.delay(500)
        matrix.reset(matrix.color('white'))
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
        new_effect = input("Enter new effect (caution, clear, medical, lastLap) or 'exit' to quit: ")
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
