# Simple test to confirm color
# Red... Green... Blue... (Repeat)
def run(matrix, config):
    """red, yellow, repeat"""
    while matrix.ready():
        matrix.reset(matrix.color('red'))
        matrix.show()
        matrix.delay(500)

        matrix.reset(matrix.color('white'))
        matrix.show()
        matrix.delay(500)

        # matrix.text('MEDICAL', (10,20), 16, (255,0,0))
        # matrix.show()
        # matrix.delay(1000)