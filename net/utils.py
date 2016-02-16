import time
from collections import namedtuple

IP_Port = namedtuple('IP_Port', ['ip', 'port'])

def looping_retry(func, *args):
    while True:
        try:
            return func(*args)
        except Exception:
            time.sleep(0.5)
