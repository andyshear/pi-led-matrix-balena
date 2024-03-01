import sys
import json
from src.led_matrix import Matrix, pixel_height, pixel_width
from PIL import Image

# Define your effects here
def effect_caution(matrix, config):
    """Red, yellow, repeat"""
    while True:
        matrix.reset(matrix.color('red'))
        matrix.show()
        matrix.delay(200)
        matrix.reset(matrix.color('yellow'))
        matrix.show()
        matrix.delay(200)

def effect_clear(matrix, config):
    """Clear the matrix"""
    matrix.reset(matrix.color('green'))
    matrix.show()

def effect_medical(matrix, config):
    """Flash red and white for medical"""
    while True:
        matrix.reset(matrix.color('red'))
        matrix.show()
        matrix.delay(500)
        matrix.reset(matrix.color('white'))
        matrix.show()
        matrix.delay(500)

def effect_lastLap(matrix, config):
    """Display white for the last lap"""
    matrix.reset(matrix.color('white'))
    matrix.show()

# Mapping of effect names to functions
effects = {
    'caution': effect_caution,
    'clear': effect_clear,
    'medical': effect_medical,
    'lastLap': effect_lastLap,
}

def swap_rgb_color(matrix):
    """Swap RGB to BGR or vice versa for the entire matrix."""
    r, g, b = matrix.frame.split()
    matrix.frame = Image.merge("RGB", (r, g, b))

def apply_effect(effect_name, matrix, config):
    """Apply an effect based on the effect name."""
    if effect_name in effects:
        effects[effect_name](matrix, config)
        swap_rgb_color(matrix)  # Assume you need to swap colors for all effects
    else:
        print(f"Unknown effect: {effect_name}")

# Main execution
if __name__ == "__main__":
    effect_name = sys.argv[1]
    matrix = Matrix()  # Initialize your matrix here
    config = {
        'pixel_height': pixel_height,
        'pixel_width': pixel_width,
        'argv': sys.argv[2:],
    }

    # Apply the selected effect
    apply_effect(effect_name, matrix, config)
