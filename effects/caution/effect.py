# Simple test to confirm color
# Red... Green... Blue... (Repeat)
def run(matrix, config):
    """red, yellow, repeat"""
    while matrix.ready():
        matrix.reset(matrix.color('red'))
        matrix.show()
        matrix.delay(200)

        matrix.reset(matrix.color('yellow'))
        matrix.show()
        matrix.delay(200)

        matrix.text('CAUTION', (10,20), 16, (255,0,0))
        matrix.show()
        matrix.delay(1000)