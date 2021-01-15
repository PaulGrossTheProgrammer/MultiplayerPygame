from time import sleep

from common import clock, frames_per_second
from timertools import timer

t = timer()

while True:
    t.on()

    # DO WORK HERE ...
    sleep(0.01)

    t.off()

    print("Average frame {}ms".format(t.avg_time_ms()))
    print("Average frame rate {}/s".format(int(t.avg_rate())))

    clock.tick(frames_per_second)