# -*- coding: utf-8 -
#
# This file is part of flower. See the NOTICE for more information.

from flower.actor import (receive, send, spawn, spawn_after, ActorRef,
        send_after, wrap, Actor)
from flower import core
from flower.time import sleep
import time

class Test_Actor:

    def test_simple(self):
        r_list = []
        def f():
            r_list.append(True)

        pid = spawn(f)
        assert isinstance(pid, ActorRef)
        assert pid.ref == 0
        assert hasattr(pid.actor, 'mailbox')

        sleep(0.1)
        core.run()

        assert r_list == [True]
        assert pid.actor is None
        assert pid.is_alive is False

    def test_wrap(self):
        r_list = []
        def f():
            r_list.append(True)

        t = core.tasklet(f)()
        assert not hasattr(t, 'mailbox')
        wrap(t)
        assert isinstance(t, Actor)
        assert hasattr(t, 'mailbox')
        assert hasattr(t, 'ref')

        pid = t.ref
        assert isinstance(pid, ActorRef)
        assert pid.ref == 1

        core.run()
        assert r_list == [True]
        assert pid.actor is None
        assert pid.is_alive is False


    def test_mailbox(self):
        messages = []
        sources = []
        def f():
            while True:
                source, msg = receive()
                if not msg:
                    break
                if source.ref not in sources:
                    sources.append(source.ref)
                messages.append(msg)

        def f1(ref):
            msg = ['hello', ' ', 'world']
            for s in msg:
                send(ref, s)

        pid0 = spawn(f)
        pid1 = spawn(f1, pid0)

        core.run()

        assert messages == ['hello', ' ', 'world']
        assert sources == [3]

    def test_multiple_producers(self):
        messages = []
        sources = []
        def f():
            while True:
                source, msg = receive()
                if not msg:
                    break
                if source.ref not in sources:
                    sources.append(source.ref)
                messages.append(msg)

        def f1(ref):
            msg = ['hello', 'world']
            for s in msg:
                send(ref, s)

        def f2(ref):
            msg = ['brave', 'new', 'world', '']
            for s in msg:
                send(ref, s)

        pid0 = spawn(f)
        pid1 = spawn(f1, pid0)
        pid2 = spawn(f2, pid0)

        core.run()

        assert len(messages) == 5
        assert sources == [5, 6]

    def test_spawn_after(self):
        r_list = []
        def f():
            r_list.append(time.time())

        start = time.time()
        spawn_after(0.3, f)

        core.run()

        end = r_list[0]
        diff = end - start
        assert 0.29 <= diff <= 0.31

    def test_send_after(self):
        r_list = []
        def f():
            receive()
            r_list.append(time.time())

        ref = spawn(f)
        start = time.time()
        send_after(0.3, ref, None)

        core.run()

        end = r_list[0]
        diff = end - start
        assert 0.29 <= diff <= 0.31
