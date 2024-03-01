# Simple test to confirm color
# Red... Green... Blue... (Repeat)
def run(matrix, config):
    # while matrix.ready():
        matrix.reset(matrix.color('green'))
        matrix.show()
        # matrix.delay(1000)