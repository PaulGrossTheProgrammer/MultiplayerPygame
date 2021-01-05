# Declare a queue, feed it from REPL, with a sleeping thread that wakes
# when the queue has anything

# Write a timing module to make it easy to print and calc elapsed times
# As well as accumulate samples for calculating stats.

import threading
import queue

import timer_tools

myq = queue.Queue()

myq.put("Stuff")
myq.get()

class MyThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        print("New Thread starting up")
        while True:
            print("THREAD WAITING for anything on the queue...")
            timer = timer_tools.timer()
            stuff = myq.get()  # .get() is a blocking method
            timer.done()
            print("THREAD waited for {}ms".format(timer.get_time_ms()))
            print("THREAD took [{}] off the queue".format(stuff))

MyThread().start()