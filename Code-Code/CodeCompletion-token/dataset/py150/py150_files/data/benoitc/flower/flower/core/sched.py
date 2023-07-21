# -*- coding: utf-8 -
#
# This file is part of flower. See the NOTICE for more information.


from collections import deque
import operator
import threading
import time

_tls = threading.local()

import greenlet
import six

from .util import thread_ident


class TaskletExit(Exception):
    pass

try:
    import __builtin__
    __builtin__.TaskletExit = TaskletExit
except ImportError:
    import builtins
    setattr(builtins, 'TaskletExit', TaskletExit)

CoroutineExit = TaskletExit
_global_task_id = 0

def _coroutine_getcurrent():
    try:
        return _tls.current_coroutine
    except AttributeError:
        return _coroutine_getmain()

def _coroutine_getmain():
    try:
        return _tls.main_coroutine
    except AttributeError:
        main = coroutine()
        main._is_started = -1
        main._greenlet = greenlet.getcurrent()
        _tls.main_coroutine = main
        return _tls.main_coroutine

class coroutine(object):
    """ simple wrapper to bind lazily a greenlet to a function """

    _is_started = 0

    def __init__(self):
        self._greenlet = greenlet

    def bind(self, func, *args, **kwargs):
        def _run():
            _tls.current_coroutine = self
            self._is_started = 1
            func(*args, **kwargs)
        self._is_started = 0
        self._greenlet = greenlet.greenlet(_run)

    def switch(self):
        current = _coroutine_getcurrent()
        try:
            self._greenlet.switch()
        finally:
            _tls.current_coroutine = current

    def kill(self):
        current = _coroutine_getcurrent()
        if self is current:
            raise CoroutineExit
        self.throw(CoroutineExit)

    def throw(self, *args):
        current = _coroutine_getcurrent()
        try:
            self._greenlet.throw(*args)
        finally:
            _tls.current_coroutine = current

    @property
    def is_alive(self):
        return self._is_started < 0 or bool(self._greenlet)

    @property
    def is_zombie(self):
        return self._is_started > 0 and bool(self._greenlet.dead)

    getcurrent = staticmethod(_coroutine_getcurrent)



def _scheduler_contains(value):
    scheduler = get_scheduler()
    return value in scheduler

def _scheduler_switch(current, next):
    scheduler = get_scheduler()
    return scheduler.switch(current, next)

class tasklet(coroutine):
    """
    A tasklet object represents a tiny task in a Python thread.
    At program start, there is always one running main tasklet.
    New tasklets can be created with methods from the stackless
    module.
    """
    tempval = None

    def __new__(cls, func=None, label=''):
        res = coroutine.__new__(cls)
        res.label = label
        res._task_id = None
        return res


    def __init__(self, func=None, label=''):
        coroutine.__init__(self)
        self._init(func, label)

    def _init(self, func=None, label=''):
        global _global_task_id
        self.func = func
        self.label = label
        self.alive = False
        self.blocked = False
        self.sched = None
        self.thread_id = thread_ident()
        self._task_id = _global_task_id
        _global_task_id += 1

    def __str__(self):
        return '<tasklet[%s, %s]>' % (self.label,self._task_id)

    __repr__ = __str__

    def __call__(self, *argl, **argd):
        return self.setup(*argl, **argd)

    def bind(self, func):
        """
        Binding a tasklet to a callable object.
        The callable is usually passed in to the constructor.
        In some cases, it makes sense to be able to re-bind a tasklet,
        after it has been run, in order to keep its identity.
        Note that a tasklet can only be bound when it doesn't have a frame.
        """
        if not six.callable(func):
            raise TypeError('tasklet function must be a callable')
        self.func = func


    def setup(self, *argl, **argd):
        """
        supply the parameters for the callable
        """
        if self.func is None:
            raise TypeError('tasklet function must be callable')
        func = self.func
        sched = self.sched = get_scheduler()

        def _func():

            try:
                try:
                    func(*argl, **argd)
                except TaskletExit:
                    pass
            finally:
                sched.remove(self)
                self.alive = False

        self.func = None
        coroutine.bind(self, _func)
        self.alive = True
        sched.append(self)
        return self

    def run(self):
        self.insert()
        _scheduler_switch(getcurrent(), self)

    def kill(self):
        if self.is_alive:
            # Killing the tasklet by throwing TaskletExit exception.
            coroutine.kill(self)

        schedrem(self)
        self.alive = False

    def raise_exception(self, exc, *args):
        if not self.is_alive:
            return
        schedrem(self)
        coroutine.throw(self, exc, *args)


    def insert(self):
        if self.blocked:
            raise RuntimeError("You cannot run a blocked tasklet")
            if not self.alive:
                raise RuntimeError("You cannot run an unbound(dead) tasklet")
        schedpush(self)

    def remove(self):
        if self.blocked:
            raise RuntimeError("You cannot remove a blocked tasklet.")
        if self is getcurrent():
            raise RuntimeError("The current tasklet cannot be removed.")
        schedrem(self)

class Scheduler(object):

    def __init__(self):
        # define the main tasklet
        self._main_coroutine = _coroutine_getmain()
        self._main_tasklet = _coroutine_getcurrent()
        self._main_tasklet.__class__ = tasklet
        six.get_method_function(self._main_tasklet._init)(self._main_tasklet,
                label='main')
        self._last_task = self._main_tasklet

        self.thread_id = thread_ident() # the scheduler thread id
        self._lock = threading.Lock() # global scheduler lock

        self._callback = None # scheduler callback
        self._run_calls = [] # runcalls. (tasks where run apply
        self.runnable = deque() # runnable tasks
        self.blocked = 0 # number of blocked/sleeping tasks
        self.append(self._main_tasklet)

    def send(self):
        self._async.send()

    def wakeup(self, handle):
        self.schedule()

    def set_callback(self, cb):
        self._callback = cb

    def append(self, value, normal=True):
        if normal:
            self.runnable.append(value)
        else:
            self.runnable.rotate(-1)
            self.runnable.appendleft(value)
            self.runnable.rotate(1)

    def appendleft(self, task):
        self.runnable.appendleft(task)

    def remove(self, task):
        """ remove a task from the runnable """

        # the scheduler need to be locked here
        with self._lock:
            try:
                self.runnable.remove(task)
                # if the task is blocked increment their number
                if task.blocked:
                    self.blocked += 1
            except ValueError:
                pass

    def unblock(self, task, normal=True):
        """ unblock a task (put back from sleep)"""
        with self._lock:
            task.blocked = 0
            self.blocked -= 1
        self.append(task, normal)

    def taskwakeup(self, task):
        if task is None:
            return

        # the scheduler need to be locked here
        with self._lock:
            try:
                self.runnable.remove(task)
            except ValueError:
                pass

        # eventually unblock the tasj
        self.unblock(task)

    def switch(self, current, next):
        prev = self._last_task
        if (self._callback is not None and prev is not next):
            self._callback(prev, next)
        self._last_task = next


        assert not next.blocked

        if next is not current:
            next.switch()

        return current

    def schedule(self, retval=None):
        curr = self.getcurrent()
        main = self.getmain()

        if retval is None:
            retval = curr

        while True:
            if self.runnable:
                if self.runnable[0] is curr:
                    self.runnable.rotate(-1)
                task = self.runnable[0]
            elif self._run_calls:
                task = self._run_calls.pop()
            else:
                raise RuntimeError("no more tasks are sleeping")


            # switch to next task
            self.switch(curr, task)

            # exit the loop if there are no more tasks
            if curr is self._last_task:
                return retval

    def run(self):
        curr = self.getcurrent()
        self._run_calls.append(curr)
        self.remove(curr)
        try:
            while True:
                self.schedule()
                if not curr.blocked:
                    break
                time.sleep(0.0001)
        finally:
            self.append(curr)

    def runcount(self):
        return len(self.runnable)

    def getmain(self):
        return self._main_tasklet

    def getcurrent(self):
        curr = _coroutine_getcurrent()
        if curr == self._main_coroutine:
            return self._main_tasklet
        else:
            return curr

    def __contains__(self, value):
        try:
            operator.indexOf(self.runnable, value)
            return True
        except ValueError:
            return False

_channel_callback = None

def set_channel_callback(channel_cb):
    global _channel_callback
    _channel_callback = channel_cb


def get_scheduler():
    global _tls
    try:
        return _tls.scheduler
    except AttributeError:
        scheduler = _tls.scheduler = Scheduler()
        return scheduler


def taskwakeup(task):
    sched = get_scheduler()
    sched.taskwakeup(task)

def getruncount():
    sched = get_scheduler()
    return sched.runcount()

def getcurrent():
    return get_scheduler().getcurrent()

def getmain():
    return get_scheduler().getmain()

def set_schedule_callback(scheduler_cb):
    sched = get_scheduler()
    sched.set_callback(scheduler_cb)

def schedule(retval=None):
    scheduler = get_scheduler()
    return scheduler.schedule(retval=retval)

def schedule_remove(retval=None):
    scheduler = get_scheduler()
    scheduler.remove(scheduler.getcurrent())
    return scheduler.schedule(retval=retval)

def schedpush(task):
    scheduler = get_scheduler()
    scheduler.append(task)

def schedrem(task):
    scheduler = get_scheduler()
    scheduler.remove(task)

def run():
    sched = get_scheduler()
    sched.run()

# bootstrap the scheduler
def _bootstrap():
    get_scheduler()
_bootstrap()
