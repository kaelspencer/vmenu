from time import time
import logging

def trace(f, *args, **kwargs):
    return tracen(f.__name__, f, *args, **kwargs)

def tracen(name, f, *args, **kwargs):
    logging.debug('%s start', name)
    start = time()
    ret = f(*args, **kwargs)
    end = time() - start
    logging.debug('%s end: %.3f', name, end)
    return ret
