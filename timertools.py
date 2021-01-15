import time

class timer():

    def __init__(self, memory=10):
        self.memory = memory
        self.start = None
        self.end = None
        self.seconds = None
        self.length_history = []  # Duration of events
        self.end_history = []  # End time of events

    def on(self):
        self.start = time.time()
        self.end = None

    def off(self):
        self.end = time.time()
        self.seconds = self.end - self.start
        self.length_history.append(self.seconds)
        self.end_history.append(self.end)
        while len(self.length_history) > self.memory:
            self.length_history.pop(0)  # Remove the oldest value

    def duration(self):
        return self.seconds

    def duration_s(self):
        return int(self.get_time())

    def duration_ms(self):
        return int(self.get_time() * 1000)

    def avg_time(self):
        if len(self.length_history) == 0:
            return 0

        total = 0
        for value in self.length_history:
            total += value

        return total/len(self.length_history)

    def avg_time_s(self):
        return int(self.avg_time())

    def avg_time_ms(self):
        return int(self.avg_time() * 1000)

    def avg_rate(self):
        if len(self.end_history) < 2:
            return 0

        diff = self.end_history[-1] - self.end_history[0]
        if diff > 0:
            return len(self.end_history)/diff
        else:
            return 0