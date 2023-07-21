# -*- coding: utf-8 -*-

__author__ = """Chris Tabor (dxdstudio@gmail.com)"""

# Concepts/learning from:
# http://inventwithpython.com/blog/2013/04/22/
#   multithreaded-python-tutorial-with-threadworms/
from Queue import Queue
import threading

if __name__ == '__main__':
    from os import getcwd
    from os import sys
    sys.path.append(getcwd())

# from random import choice
from MOAL.helpers.text import gibberish
from MOAL.helpers.display import Section


COUNT_LOCK = threading.Lock()
DEBUG = True if __name__ == '__main__' else False
total = 1


class CountThread(threading.Thread):

    def start(self, name):
        # Allow adding a name when start is called,
        # but still defer to superclass method
        self.name = name
        super(CountThread, self).start()

    def run(self):
        # Make total a global variable, outside the scope of this
        # function/class to demonstrate the thread updates
        global total
        for i in range(1000):
            # Must acquire and then release lock after every operation,
            # otherwise the global mutable state will be overwritten for each
            # thread that runs, resetting the value, which is significantly
            # lower than the correct total.
            COUNT_LOCK.acquire()
            total += 1
            COUNT_LOCK.release()
        if DEBUG:
            print('Total processed by {}: {}:'.format(self.name, total))


class Worker:

    def __init__(self, queue, num_threads=2):
        self.NUM_THREADS = num_threads
        self.queue = queue

    def do_work(self, item):
        if DEBUG:
            print('Working on item... {}\n'.format(item))

    def worker(self):
        while True:
            item = self.queue.get()
            self.do_work(item)
            self.queue.task_done()

    def process_all(self):
        if DEBUG:
            print('Starting all process threads...')
        for _ in range(self.NUM_THREADS):
            t = threading.Thread(target=self.worker)
            t.daemon = True
            t.start()


class Producer:

    def __init__(self):
        self.items = []

    def __iter__(self):
        for record in self.items:
            yield record
        raise StopIteration

    def add(self):
        self.items.append(self.make())

    def make(self):
        return gibberish()


if DEBUG:
    with Section('Python stdlib Queue and multi-threading examples'):
        counter_one = CountThread()
        counter_two = CountThread()
        counter_three = CountThread()
        counter_one.start('one')
        counter_two.start('two')
        counter_three.start('three')

    # Some basic code taken from docs.python.org/2/library/queue.html

    with Section('Python stdlib Queue and multi-threading examples 2'):
        work_queue = Queue()
        bot = Worker(work_queue)
        producer = Producer()

        for _ in range(10):
            producer.add()

        for record in producer:
            print('Putting record {} into queue.'.format(record))
            work_queue.put(record)

        bot.process_all()

        # Block until done
        work_queue.join()
