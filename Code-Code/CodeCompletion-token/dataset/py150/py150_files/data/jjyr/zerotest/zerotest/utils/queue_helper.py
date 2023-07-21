try:
    from Queue import Queue, Empty
except ImportError:
    # python3
    from queue import Queue, Empty
