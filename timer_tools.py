import time

class timer():

    def __init__(self):
        self.start = time.time()
        self.end = None
        self.seconds = None

    def done(self):
        self.end = time.time()
        self.seconds = self.end - self.start

    def get_time_s(self):
        return int(self.seconds)

    def get_time_ms(self):
        return int(self.seconds * 1000)