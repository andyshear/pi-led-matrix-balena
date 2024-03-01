import sys
from lights.effect import apply_effect, effect_caution, effect_clear, effect_medical, effect_lastLap, swap_rgb_color
from your_matrix_library import Matrix # Import or define your matrix manipulation class

# Assume the first argument is the effect name
effect_name = sys.argv[1]

# Initialize your matrix here
matrix = Matrix()  # This should be an instance of your matrix manipulation class
config = {}  # Any configuration needed

effects = {
    'caution': effect_caution,
    'clear': effect_clear,
    # Add more effects here
}

if effect_name in effects:
    apply_effect(matrix, effects[effect_name], config)
    swap_rgb_color(matrix)
else:
    print(f"Unknown effect: {effect_name}")
