import sys
import json
from src.led_matrix import Matrix, pixel_height, pixel_width
from PIL import Image

# Initialize global variables for effect control
current_effect = None
matrix = Matrix()  # Initialize your matrix here

def effect_caution(matrix, config):
    """Red, yellow, repeat"""
    global current_effect
    while current_effect == 'caution':
        matrix.reset(matrix.color('red'))
        matrix.show()
        matrix.delay(200)
        matrix.reset(matrix.color('yellow'))
        matrix.show()
        matrix.delay(200)

def effect_clear(matrix, config):
    """Clear the matrix"""
    global current_effect
    if current_effect == 'clear':
        matrix.reset(matrix.color('green'))
        matrix.show()

def effect_medical(matrix, config):
    """Flash red and white for medical"""
    global current_effect
    while current_effect == 'medical':
        matrix.reset(matrix.color('red'))
        matrix.show()
        matrix.delay(500)
        matrix.reset(matrix.color('white'))
        matrix.show()
        matrix.delay(500)

def effect_lastLap(matrix, config):
    """Display white for the last lap"""
    global current_effect
    if current_effect == 'lastLap':
        matrix.reset(matrix.color('white'))
        matrix.show()

# Mapping of effect names to functions
effects = {
    'caution': effect_caution,
    'clear': effect_clear,
    'medical': effect_medical,
    'lastLap': effect_lastLap,
}

def apply_effect(effect_name, config):
    """Apply an effect based on the effect name."""
    global current_effect
    current_effect = effect_name  # Update the current effect
    if effect_name in effects:
        effects[effect_name](matrix, config)
    else:
        print(f"Unknown effect: {effect_name}")

def listen_for_commands():
    """Continuously listen for new commands and apply effects accordingly."""
    global current_effect
    while True:
        # This is a placeholder for the actual command listening mechanism.
        # It could be reading from a queue, socket, or another inter-process communication method.
        # For demonstration, simulate receiving a command via standard input.
        new_effect = input("Enter new effect (caution, clear, medical, lastLap) or 'exit' to quit: ")
        if new_effect == 'exit':
            break
        apply_effect(new_effect, {
            'pixel_height': pixel_height,
            'pixel_width': pixel_width,
            # Add additional config as needed
        })

if __name__ == "__main__":
    # Start by applying the effect passed as an argument, if any
    initial_effect = sys.argv[1] if len(sys.argv) > 1 else None
    if initial_effect:
        apply_effect(initial_effect, {
            'pixel_height': pixel_height,
            'pixel_width': pixel_width,
            'argv': sys.argv[2:],
        })
    # Then listen for new commands
    listen_for_commands()
