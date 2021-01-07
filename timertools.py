import time

class timer():

    def __init__(self, memory=10):
        self.memory = memory
        self.start = None
        self.end = None
        self.seconds = None
        self.history = []

    def on(self):
        self.start = time.time()
        self.end = None

    def off(self):
        self.end = time.time()
        self.seconds = self.end - self.start
        self.history.append(self.seconds)
        while len(self.history) > self.memory:
            self.history.pop(0)  # Remove the oldest value

    def get_time(self):
        return self.seconds

    def get_time_s(self):
        return int(self.get_time())

    def get_time_ms(self):
        return int(self.get_time() * 1000)

    def get_avgtime(self):
        if len(self.history) == 0:
            return 0

        total = 0
        for value in self.history:
            total += value

        return total/len(self.history)

    def get_avgtime_s(self):
        return int(self.get_avgtime())

    def get_avgtime_ms(self):
        return int(self.get_avgtime() * 1000)