from PIL import Image

def apply_effect(matrix, effect_function, config):
    """
    Apply an effect function to the matrix.
    The effect function should take a matrix and a config, and manipulate the matrix directly.
    """
    effect_function(matrix, config)
    matrix.show()

def swap_rgb_color(matrix):
    """
    Swap RGB to BGR or vice versa for the entire matrix.
    This function is called after an effect function has finished processing the matrix.
    """
    b, g, r = matrix.frame.split()
    matrix.frame = Image.merge('RGB', (r, g, b))

def effect_caution(matrix, config):
    # Implement the caution effect here.
    # Example:
    matrix.reset(matrix.color('red'))
    matrix.delay(200)
    matrix.reset(matrix.color('yellow'))
    matrix.delay(200)

def effect_clear(matrix, config):
    # Implement the clear effect here.
    matrix.reset(matrix.color('green'))

def effect_medical(matrix, config):
    # Implement the caution effect here.
    # Example:
    matrix.reset(matrix.color('red'))
    matrix.delay(500)
    matrix.reset(matrix.color('white'))
    matrix.delay(500)

def effect_lastLap(matrix, config):
    # Implement the clear effect here.
    matrix.reset(matrix.color('white'))
