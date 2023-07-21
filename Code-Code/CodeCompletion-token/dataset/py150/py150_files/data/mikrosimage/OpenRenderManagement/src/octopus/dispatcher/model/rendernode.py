####################################################################################################
# @file rendernode.py
# @package dispatcher.model
# @author
# @date 2008/10/29
# @version 0.1
#
# @mainpage
#
####################################################################################################

import httplib as http
import time
import datetime
import logging
import errno
import requests
from collections import deque

from octopus.dispatcher.model.enums import *
from octopus.dispatcher import settings
from octopus.core import singletonconfig

from . import models

LOGGER = logging.getLogger('main.dispatcher.webservice')
logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARNING)


class RenderNode(models.Model):
    '''This class represents the state of a RenderNode.'''

    # Sys infos
    name = models.StringField()
    speed = models.FloatField()
    coresNumber = models.IntegerField()
    ramSize = models.IntegerField()

    # Dynamic sys infos
    freeCoresNumber = models.IntegerField()
    usedCoresNumber = models.DictField(as_item_list=True)
    freeRam = models.IntegerField()
    systemFreeRam = models.IntegerField()
    systemSwapPercentage = models.FloatField()
    usedRam = models.DictField(as_item_list=True)

    # Worker state
    puliversion = models.StringField()
    commands = models.ModelDictField()
    status = models.IntegerField()
    host = models.StringField()
    port = models.IntegerField()
    pools = models.ModelListField(indexField='name')
    caracteristics = models.DictField()
    isRegistered = models.BooleanField()
    performance = models.FloatField()
    excluded = models.BooleanField()

    # Timers
    createDate = models.FloatField()
    registerDate = models.FloatField()
    lastAliveTime = models.FloatField()

    def __init__(self, id, name, coresNumber, speed, ip, port, ramSize, caracteristics=None, performance=0.0, puliversion="undefined", createDate=None):
        '''Constructs a new Rendernode.

        :parameters:
        - `name`: the name of the rendernode
        - `coresNumber`: the number of processors
        - `speed`: the speed of the processor
        '''
        self.id = int(id) if id else None
        self.name = str(name)

        self.coresNumber = int(coresNumber)
        self.ramSize = int(ramSize)
        self.licenseManager = None
        self.freeCoresNumber = int(coresNumber)
        self.usedCoresNumber = {}
        self.freeRam = int(ramSize)  # ramSize-usedRam i.e. the amount of RAM used if several commands running concurrently
        self.systemFreeRam = int(ramSize)  # the RAM available on the system (updated each ping)
        self.systemSwapPercentage = 0
        self.usedRam = {}

        self.speed = speed
        self.commands = {}
        self.status = RN_UNKNOWN
        self.responseId = None
        self.host = str(ip)
        self.port = int(port)
        self.pools = []
        self.idInformed = False
        self.isRegistered = False
        self.lastAliveTime = 0
        self.httpConnection = None
        self.caracteristics = caracteristics if caracteristics else {}
        self.currentpoolshare = None
        self.performance = float(performance)
        self.history = deque(maxlen=singletonconfig.get('CORE', 'RN_NB_ERRORS_TOLERANCE'))
        self.tasksHistory = deque(maxlen=15)
        self.excluded = False

        # Init new data
        self.puliversion = puliversion
        if createDate is None:
            self.createDate = 0
        else:
            self.createDate = createDate

        self.registerDate = time.time()

        # Flag linked to the worker flag "isPaused". Handles the case when a worker is set paused but a command is still running (finishing)
        # the RN on the dispatcher must be flag not to be assigned (i.e. in isAvailable property)
        # self.canBeAssigned = True

        if not "softs" in self.caracteristics:
            self.caracteristics["softs"] = []

    ## Returns True if this render node is available for command assignment.
    #
    def isAvailable(self):
        # Need to avoid nodes that have flag isPaused set (i.e. nodes paused by user but still running a command)
        return (self.isRegistered and self.status == RN_IDLE and not self.commands and not self.excluded)

    def reset(self, paused=False):
        # if paused, set the status to RN_PAUSED, else set it to Finishing, it will be set to IDLE in the next iteration of the dispatcher main loop
        if paused:
            self.status = RN_PAUSED
        else:
            self.status = RN_FINISHING
        # reset the commands left on this RN, if any
        for cmd in self.commands.values():
            cmd.status = CMD_READY
            cmd.completion = 0.
            cmd.renderNode = None
            self.clearAssignment(cmd)
        self.commands = {}
        # reset the associated poolshare, if any
        if self.currentpoolshare:
            self.currentpoolshare.allocatedRN -= 1
            self.currentpoolshare = None
        # reset the values for cores and ram
        self.freeCoresNumber = int(self.coresNumber)
        self.usedCoresNumber = {}
        self.freeRam = int(self.ramSize)
        self.usedRam = {}

    ## Returns a human readable representation of this RenderNode.
    #
    def __repr__(self):
        return u'RenderNode(id=%s, name=%s, host=%s, port=%s)' % (repr(self.id), repr(self.name), repr(self.host), repr(self.port))

    ## Clears all of this rendernode's fields related to the specified assignment.
    #
    def clearAssignment(self, command):
        '''Removes command from the list of commands assigned to this rendernode.'''
        # in case of failed assignment, decrement the allocatedRN value
        if self.currentpoolshare:
            self.currentpoolshare.allocatedRN -= 1
            self.currentpoolshare = None
        try:
            del self.commands[command.id]
        except KeyError:
            pass
            #LOGGER.debug('attempt to clear assignment of not assigned command %d on worker %s', command.id, self.name)
        else:
            self.releaseRessources(command)
            self.releaseLicense(command)

    ## Add a command assignment
    #
    def addAssignment(self, command):
        if not command.id in self.commands:
            self.commands[command.id] = command
            self.reserveRessources(command)
            # FIXME the assignment of the cmd should be done here and not in the dispatchIterator func
            command.assign(self)
            self.updateStatus()

    ## Reserve license
    #
    def reserveLicense(self, command, licenseManager):
        self.licenseManager = licenseManager
        lic = command.task.lic
        if not lic:
            return True
        return licenseManager.reserveLicenseForRenderNode(lic, self)

    ## Release licence
    #
    def releaseLicense(self, command):
        lic = command.task.lic
        if lic and self.licenseManager:
            self.licenseManager.releaseLicenseForRenderNode(lic, self)

    ## Reserve ressource
    #
    def reserveRessources(self, command):
        res = min(self.freeCoresNumber, command.task.maxNbCores) or self.freeCoresNumber
        self.usedCoresNumber[command.id] = res
        self.freeCoresNumber -= res

        res = min(self.freeRam, command.task.ramUse) or self.freeRam

        self.usedRam[command.id] = res
        self.freeRam -= res

    ## Release ressource
    #
    def releaseRessources(self, command):
        #res = self.usedCoresNumber[command.id]
        self.freeCoresNumber = self.coresNumber
        if command.id in self.usedCoresNumber:
            del self.usedCoresNumber[command.id]

        #res = self.usedRam[command.id]
        self.freeRam = self.ramSize
        if command.id in self.usedRam:
            del self.usedRam[command.id]

    ## Unassign a finished command
    #
    def unassign(self, command):
        if not isFinalStatus(command.status):
            raise ValueError("cannot unassign unfinished command %s" % repr(command))
        self.clearAssignment(command)
        self.updateStatus()

    def remove(self):
        self.fireDestructionEvent(self)

    def updateStatus(self):
        """
        Update rendernode status according to its states: having commands or not, commands status, time etc
        Status is not changed if no info is brought by the commands.
        """
        # self.status is not RN_PAUSED and time elapsed is enough
        if time.time() > (self.lastAliveTime + singletonconfig.conf["COMMUNICATION"]["RN_TIMEOUT"]):

            # set the status of a render node to RN_UNKNOWN after TIMEOUT seconds have elapsed since last update
            # timeout the commands running on this node
            if RN_UNKNOWN != self.status:
                LOGGER.warning("rendernode %s is not responding", self.name)
                self.status = RN_UNKNOWN
                if self.commands:
                    for cmd in self.commands.values():
                        cmd.status = CMD_TIMEOUT
                        self.clearAssignment(cmd)
            return
        # This is necessary in case of a cancel command or a mylawn -k
        if not self.commands:
            # if self.status is RN_WORKING:
            #     # cancel the command that is running on this RN because it's no longer registered in the model
            #     LOGGER.warning("rendernode %s is reported as working but has no registered command" % self.name)
            if self.status not in (RN_IDLE, RN_PAUSED, RN_BOOTING):
                #LOGGER.warning("rendernode %s was %d and is now IDLE." % (self.name, self.status))
                self.status = RN_IDLE
                if self.currentpoolshare:
                    self.currentpoolshare.allocatedRN -= 1
                    self.currentpoolshare = None
            return
        commandStatus = [command.status for command in self.commands.values()]
        if CMD_RUNNING in commandStatus:
            self.status = RN_WORKING
        elif CMD_ASSIGNED in commandStatus:
            self.status = RN_ASSIGNED
        elif CMD_ERROR in commandStatus:
            self.status = RN_FINISHING
        elif CMD_FINISHING in commandStatus:
            self.status = RN_FINISHING
        elif CMD_DONE in commandStatus:
            self.status = RN_FINISHING  # do not set the status to IDLE immediately, to ensure that the order of affectation will be respected

        elif CMD_TIMEOUT in commandStatus:
            self.status = RN_FINISHING

        elif CMD_CANCELED in commandStatus:
            for cmd in self.commands.values():
                # this should not happened, but if it does, ensure the command is no more registered to the rn
                if cmd.status is CMD_CANCELED:
                    self.clearAssignment(cmd)
        elif self.status not in (RN_IDLE, RN_BOOTING, RN_UNKNOWN, RN_PAUSED):
            LOGGER.error("Unable to compute new status for rendernode %r (status %r, commands %r)", self, self.status, self.commands)

    ## releases the finishing status of the rendernodes
    #
    def releaseFinishingStatus(self):
        if self.status is RN_FINISHING:
            # remove the commands that are in a final status
            for cmd in self.commands.values():
                if isFinalStatus(cmd.status):
                    self.unassign(cmd)
                    if CMD_DONE == cmd.status:
                        cmd.completion = 1.0
                    cmd.finish()
            self.status = RN_IDLE

    ##
    #
    # @warning The returned HTTPConnection is not safe to use from multiple threads
    #
    def getHTTPConnection(self):
        timeout = singletonconfig.get('COMMUNICATION', 'RENDERNODE_REQUEST_TIMEOUT', 5)
        return http.HTTPConnection(self.host, self.port, timeout=timeout)

    ## An exception class to report a render node http request failure.
    #
    class RequestFailed(Exception):
        pass

    ## Sends a HTTP request to the render node and returns a (HTTPResponse, data) tuple on success.
    #
    # This method tries to send the request at most RENDERNODE_REQUEST_MAX_RETRY_COUNT times,
    # waiting RENDERNODE_REQUEST_DELAY_AFTER_REQUEST_FAILURE seconds between each try. It
    # then raises a RenderNode.RequestFailed exception.
    #
    # @param method the HTTP method for this request
    # @param url the requested URL
    # @param headers a dictionary with string-keys and string-values (empty by default)
    # @param body the string body for this request (None by default)
    # @raise RenderNode.RequestFailed if the request fails.
    # @note it is a good idea to specify a Content-Length header when giving a non-empty body.
    # @see  the RENDERNODE_REQUEST_MAX_RETRY_COUNT and
    #       RENDERNODE_REQUEST_DELAY_AFTER_REQUEST_FAILURE params affect the execution of this method.
    #
    def request(self, method, url, body=None, headers={}):
        """
        """

        # from octopus.dispatcher import settings
        # LOGGER.debug("Send request to RN: http://%s:%s%s %s (%s)" % (self.host, self.port, url, method, headers))

        err = None
        conn = self.getHTTPConnection()

        # try to process the request at most RENDERNODE_REQUEST_MAX_RETRY_COUNT times.
        for i in xrange(singletonconfig.get('COMMUNICATION', 'RENDERNODE_REQUEST_MAX_RETRY_COUNT')):
            try:
                conn.request(method, url, body, headers)
                response = conn.getresponse()
                if response.length:
                    data = response.read(response.length)
                else:
                    data = None
                # request succeeded
                conn.close()
                return (response, data)
            except http.socket.error, e:
                err = e
                # LOGGER.debug("socket error %r" % e)
                try:
                    conn.close()
                except:
                    pass
                if e in (errno.ECONNREFUSED, errno.ENETUNREACH):
                    raise self.RequestFailed(cause=e)
            except http.HTTPException, e:
                err = e
                # LOGGER.debug("HTTPException %r" % e)
                try:
                    conn.close()
                except:
                    pass
                LOGGER.exception("rendernode.request failed")

            LOGGER.warning("request failed (%d/%d), reason: %s" % (i + 1, singletonconfig.get('COMMUNICATION', 'RENDERNODE_REQUEST_MAX_RETRY_COUNT'), err))
            # request failed so let's sleep for a while
            time.sleep(singletonconfig.get('COMMUNICATION', 'RENDERNODE_REQUEST_DELAY_AFTER_REQUEST_FAILURE'))

        # request failed too many times so reset the RN (without pausing) and set quarantine
        self.reset(paused=False)
        self.excluded = True
        LOGGER.warning("A network call to the node %s can not be completed --> put in quarantine" % (self.name))
        raise self.RequestFailed()

    def canRun(self, command):
        # check if this rendernode has made too much errors in its last commands
        cpt = 0
        for i in self.history:
            if i == CMD_ERROR:
                cpt += 1
        if cpt == singletonconfig.get('CORE', 'RN_NB_ERRORS_TOLERANCE'):
            LOGGER.warning("RenderNode %s had only errors in its commands history, excluding..." % self.name)
            self.excluded = True
            return False
        if self.excluded:
            return False
        for (requirement, value) in command.task.requirements.items():
            if requirement.lower() == "softs":  # todo
                for soft in value:
                    if not soft in self.caracteristics['softs']:
                        return False
            else:
                if not requirement in self.caracteristics:
                    return False
                else:
                    caracteristic = self.caracteristics[requirement]
                    if type(caracteristic) != type(value) and not isinstance(value, list):
                        return False
                    if isinstance(value, list) and len(value) == 2:
                        a, b = value
                        if type(a) != type(b) or type(a) != type(caracteristic):
                            return False
                        try:
                            if not (a < caracteristic < b):
                                return False
                        except ValueError:
                            return False
                    else:
                        if isinstance(caracteristic, bool) and caracteristic != value:
                            return False
                        if isinstance(caracteristic, basestring) and caracteristic != value:
                            return False
                        if isinstance(caracteristic, int) and caracteristic < value:
                            return False

        if command.task.minNbCores:
            if self.freeCoresNumber < command.task.minNbCores:
                return False
        else:
            if self.freeCoresNumber != self.coresNumber:
                return False

        #
        # RAM requirement: we check task requirement with the amount of free RAM reported at last ping (systemFreeRam)
        #
        if command.task.ramUse != 0:
            if self.systemFreeRam < command.task.ramUse:
                LOGGER.info("Not enough ram on %s for command %d. %d needed, %d avail." % (self.name, command.id, int(command.task.ramUse), self.systemFreeRam))
                return False

        #
        # timer requirements: a timer is on the task and is the same for all commands
        #
        if command.task.timer is not None:
            # LOGGER.debug("Current command %r has a timer : %s" % (command.id, datetime.datetime.fromtimestamp(command.task.timer) ) )
            if time.time() < command.task.timer:
                LOGGER.info("Prevented execution of command %d because of timer present (%s)" % (command.id, datetime.datetime.fromtimestamp(command.task.timer)))
                return False

        return True
