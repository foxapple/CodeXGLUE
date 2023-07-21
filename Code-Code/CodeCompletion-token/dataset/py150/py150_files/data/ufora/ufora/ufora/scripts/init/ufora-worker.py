#!/usr/bin/env python

#   Copyright 2015 Ufora Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import argparse
import os
import signal
import socket
import sys

import ufora.config.Config as Config
import ufora.config.Setup as Setup
import ufora.cumulus.distributed.CumulusService as CumulusService
import ufora.distributed.S3.ActualS3Interface as ActualS3Interface
import ufora.distributed.SharedState.Connections.ViewFactory as ViewFactory
import ufora.distributed.SharedState.Connections.TcpChannelFactory as TcpChannelFactory
import ufora.distributed.Storage.NullObjectStore as NullObjectStore
import ufora.native.CallbackScheduler as CallbackScheduler
import ufora.native.Cumulus as CumulusNative
from ufora.networking.MultiChannelListener import MultiChannelListener

def get_own_ip():
    try:
        return socket.gethostbyname(socket.getfqdn())
    except socket.gaierror:
        return '127.0.0.1'

def createArgumentParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p',
                        '--base-port',
                        type=int,
                        default=os.getenv("UFORA_WORKER_BASE_PORT", 30009),
                        help=("The lower of two consecutive port numbers used by ufora-worker. "
                              "Default: %(default)s"))

    parser.add_argument('-a',
                        '--own-address',
                        default=os.getenv("UFORA_WORKER_OWN_ADDRESS", None),
                        help="The IP address that this worker should bind to.")


    parser.add_argument('-m',
                        '--manager-address',
                        default=os.getenv("UFORA_MANAGER_ADDRESS", "localhost"),
                        help=("The address of the Ufora manager service. "
                              "Default: %(default)s"))

    parser.add_argument('--manager-port',
                        default=os.getenv("UFORA_MANAGER_PORT", 30002),
                        help=("The port of the Ufora manager service. "
                              "Default: %(default)s"))

    return parser


def createEventHandler(events_dir, callback_scheduler):
    if not os.path.isdir(events_dir):
        os.makedirs(events_dir)
    return CumulusNative.CumulusWorkerWriteToDiskEventHandler(
        callback_scheduler,
        os.path.join(events_dir, "ufora-worker-events.%s.log" % os.getpid())
        )


def createService(args):
    callbackSchedulerFactory = CallbackScheduler.createSimpleCallbackSchedulerFactory()
    callbackScheduler = callbackSchedulerFactory.createScheduler('ufora-worker', 1)
    channelListener = MultiChannelListener(callbackScheduler,
                                           [args.base_port, args.base_port + 1])

    sharedStateViewFactory = ViewFactory.ViewFactory.TcpViewFactory(
        callbackSchedulerFactory.createScheduler('SharedState', 1),
        args.manager_address,
        int(args.manager_port)
        )

    channelFactory = TcpChannelFactory.TcpStringChannelFactory(callbackScheduler)

    diagnostics_dir = os.getenv("UFORA_WORKER_DIAGNOSTICS_DIR")
    eventHandler = diagnostics_dir and createEventHandler(
        diagnostics_dir,
        callbackSchedulerFactory.createScheduler("ufora-worker-event-handler", 1)
        )

    own_address = args.own_address or get_own_ip()
    print "Listening on", own_address, "ports:", args.base_port, "and", args.base_port+1

    return CumulusService.CumulusService(
        own_address,
        channelListener,
        channelFactory,
        eventHandler,
        callbackScheduler,
        diagnostics_dir,
        Setup.config(),
        viewFactory=sharedStateViewFactory,
        s3InterfaceFactory=ActualS3Interface.ActualS3InterfaceFactory(),
        objectStore=NullObjectStore.NullObjectStore()
        )

def defaultSetup():
    return Setup.Setup(Config.Config({}))

def main(args):
    print "ufora-worker starting"
    setup = defaultSetup()
    with Setup.PushSetup(setup):
        setup.config.configureLoggingForBackgroundProgram()
        
        worker = createService(args)
        worker.startService(None)

        def signal_handler(sig, _):
            signal_name = '(unknown)'
            if sig == signal.SIGINT:
                signal_name = 'SIGINT'
            elif sig == signal.SIGTERM:
                signal_name = 'SIGTERM'

            print 'Received ', signal_name, 'signal. Exiting.'

            worker.stopService()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        print "Press Ctrl+C to exit."
        signal.pause()


if __name__ == "__main__":
    main(createArgumentParser().parse_args())

