import threading
import queue  # Thread-safe queue

from time import sleep

import timertools

class SimpleThread(threading.Thread):

    def run(self):
        print("Starting")
        sleep(1)
        print("End")

SimpleThread().start()

q = queue.Queue()

class QThread(threading.Thread):

    def run(self):
        print("New Thread starting up")
        t = timertools.timer()
        while True:
            print("THREAD WAITING for anything on the queue...")
            t.on()
            stuff = q.get()  # .get() is a blocking method
            # Only the scheduler can wake up this thread.
            t.off()
            print(t.get_avgtime_ms())

            print("THREAD took [{}] off the queue".format(stuff))

QThread().start()

def tank_litres(analog_read):
    return (1024 - analog_read) * 1000/1024