import time
import random

n = 10  # no of pframes
p = 0.35 # probability of packet get lost
s = 0

while s < n:
    print(f"Sending Frame no {s}")
    ack = False
    while not ack:
        time.sleep(1)
        if random.random() < p:
            print(f"Frame no {s} lost, retransmitting again...")
            print(f"Sending Frame no {s}")
        else:
            print(f"ack {s} received")
            ack = True
    s += 1