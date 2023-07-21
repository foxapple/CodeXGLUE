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

import ufora.util.SubprocessingModified as subprocess
import os
import fcntl
import time
import select
import threading
import logging
import Queue
import traceback
import ufora.util.ManagedThread as ManagedThread

setupLock = threading.Lock()

class SubprocessRunner(object):
    def __init__(self,
                 subprocessArguments,
                 onStdOut,
                 onStdErr,
                 env=None,
                 enablePartialLineOutput=False):
        self.onStdOut = onStdOut
        self.onStdErr = onStdErr
        self.subprocessArguments = subprocessArguments
        self.env = env

        self.enablePartialLineOutput = enablePartialLineOutput
        self.pipeReadBufferSize = 1024

        self.onDisconnected = None
        self.subprocessOutThread = None
        self.isShuttingDown = False
        self.process = None
        self.isStarted = False
        self.messagePumpThread = None
        self.messagePumpQueue = Queue.Queue()

        self.subprocessStdIn = None
        self.subprocessStdOut = None
        self.subprocessStdErr = None
        self.subprocessOutputThread = None

    def start(self):
        with setupLock:
            assert self.subprocessOutThread is None or not self.subprocessOutThread.is_alive()

            stdInRead, stdInWrite = os.pipe()
            stdOutRead, stdOutWrite = os.pipe()
            stdErrRead, stdErrWrite = os.pipe()

            self.subprocessStdIn = os.fdopen(stdInWrite, 'w', 1)
            self.subprocessStdOut = os.fdopen(stdOutRead, 'r', 1)
            self.subprocessStdErr = os.fdopen(stdErrRead, 'r', 1)


            if self.enablePartialLineOutput:
                # enable non-blocking reads
                fcntl.fcntl(self.subprocessStdOut, fcntl.F_SETFL, os.O_NONBLOCK)
                fcntl.fcntl(self.subprocessStdErr, fcntl.F_SETFL, os.O_NONBLOCK)


            self.subprocessStdInFileDescriptor = stdInWrite
            self.subprocessStdOutFileDescriptor = stdOutRead
            self.subprocessStdErrFileDescriptor = stdErrRead

            self.subprocessStdOutFromOtherSide = os.fdopen(stdOutWrite, 'w', 1)
            self.subprocessStdErrFromOtherSide = os.fdopen(stdErrWrite, 'w', 1)

            #start our reading threads BEFORE we open the process
            self.subprocessOutThread = ManagedThread.ManagedThread(
                target=self.processOutputLoop,
                args=('stdOut', self.subprocessStdOut, self.onStdOut)
                )

            self.subprocessOutThread.start()

            self.subprocessErrThread = ManagedThread.ManagedThread(
                target=self.processOutputLoop,
                args=('stdErr', self.subprocessStdErr, self.onStdErr)
                )
            self.subprocessErrThread.start()

            logging.debug("SubprocessRunner subprocess.Popen call starting with arguments %s",
                          self.subprocessArguments)

            subprocessEvent = threading.Event()
            def startSubprocess():
                self.process = subprocess.Popen(
                        self.subprocessArguments,
                        stdin=stdInRead,
                        stdout=stdOutWrite,
                        stderr=stdErrWrite,
                        env=self.env
                        )
                subprocessEvent.set()

            startSubprocessThread = ManagedThread.ManagedThread(target=startSubprocess)
            startSubprocessThread.start()

            subprocessEvent.wait(10.0)

            if not subprocessEvent.isSet():
                import ufora.native.TCMalloc as TCMallocNative
                logging.error("Failed to start subprocess: Total MB used: %s", TCMallocNative.getBytesUsed() / 1024 / 1024.0)
            assert subprocessEvent.isSet(), "Failed to start the subprocess process."

            os.close(stdInRead)

            self.isStarted = True
            # return self to allow chaining like: runner.start().wait(...)
            return self

    @property
    def pid(self):
        if self.process is None:
            return None
        else:
            return self.process.pid

    def __str__(self):
        return "Subprocess(isStarted=%s, args=%s)" % (self.isStarted, self.subprocessArguments)

    def write(self, content):
        assert self.isStarted, "Process is not started."
        self.subprocessStdIn.write(content)

    def flush(self):
        self.subprocessStdIn.flush()

    def stop(self):
        try:
            if self.process:
                #disconnect the subprocess
                try:
                    result = self.process.poll()
                    if result is None:
                        self.process.kill()
                except OSError:
                    pass

                self.process.wait()
                logging.debug("Subprocess has shut down successfully")

            self.isShuttingDown = True

            if self.subprocessOutThread is not None and not self.isSuprocessOutThread():
                self.subprocessStdOutFromOtherSide.write("\n")
                self.subprocessOutThread.join()
                self.subprocessStdOutFromOtherSide.close()

            if self.subprocessErrThread is not None and not self.isSuprocessErrThread():
                self.subprocessStdErrFromOtherSide.write("\n")
                self.subprocessErrThread.join()
                self.subprocessStdErrFromOtherSide.close()

            self.subprocessStdIn.close()

            logging.debug("SubprocessRunner has shut down successfully")
        finally:
            self.isShuttingDown = False

    def terminate(self):
        assert self.isStarted
        self.process.terminate()

    def wait(self, timeout=None, interval=.1):
        if timeout is None:
            return self.process.wait()

        toStopTime = time.time() + timeout
        while self.process.poll() is None and time.time() < toStopTime:
            time.sleep(interval)

        return self.process.poll()

    def isSuprocessOutThread(self):
        return threading.currentThread().ident == self.subprocessOutThread.ident

    def isSuprocessErrThread(self):
        return threading.currentThread().ident == self.subprocessOutThread.ident


    def processOutputLoop(self, description, outputFile, onDataCallback):
        try:
            while not self.isShuttingDown:
                if self.enablePartialLineOutput:
                    r = select.select([outputFile], [], [])[0]
                    if len(r):
                        stdErrMessage = r[0].read(self.pipeReadBufferSize)
                else:
                    stdErrMessage = outputFile.readline().rstrip()
                try:
                    if not self.isShuttingDown:
                        onDataCallback(stdErrMessage)
                except:
                    logging.error("%s threw exception: %s",
                                  onDataCallback.__name__,
                                  traceback.format_exc())
        finally:
            logging.debug("SubprocessRunner closing %s to subprocess", description)
            outputFile.close()



def callAndReturnResultWithoutOutput(args, timeout=60.0, env=None):
    process = SubprocessRunner(args, lambda msg: None, lambda msg: None, env=env)
    process.start()
    result = process.wait(timeout)
    process.stop()

    assert result is not None, "Subprocess failed to return: %s" % args
    return result

def callAndReturnResultAndOutput(args, timeout=60.0, env=None):
    stdOut = []
    stdErr = []

    process = SubprocessRunner(args, stdOut.append, stdErr.append, env=env)
    process.start()
    result = process.wait(timeout)
    process.stop()

    return result, stdOut, stdErr

def callAndAssertSuccess(args, timeout=60.0, env=None):
    res, out, err = callAndReturnResultAndOutput(args, timeout=timeout, env=env)

    if res != 0.0:
        print "failed " + " ".join(args)
        print "captured out: "
        print "----------------------"
        print "\n".join(out)
        print "----------------------"

        print "captured err: "
        print "----------------------"
        print "\n".join(err)
        print "----------------------"

        assert False

def callAndReturnOutput(args, timeout=60.0, env=None):
    result, out, _ = callAndReturnResultAndOutput(args, timeout, env=env)
    if result is None:
        return None
    return "\n".join(out)


