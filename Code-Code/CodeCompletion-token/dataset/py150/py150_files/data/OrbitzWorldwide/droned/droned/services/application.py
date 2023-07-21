###############################################################################
#   Copyright 2006 to the present, Orbitz Worldwide, LLC.
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
###############################################################################

from kitt.interfaces import moduleProvides, IDroneDService
moduleProvides(IDroneDService) #requirement

__doc__ = """
The application service is responsible for configuring and managing the life
cycle of AppManager models.  It will scan crashed AppInstance models and fire
events accordingly.  This service is driven completely of of romeo.
"""

from twisted.python.failure import Failure
from twisted.internet import task, defer
from twisted.application.service import Service
from droned.logging import logWithContext, err
from kitt.proc import listProcesses, isRunning
from kitt.util import crashReport, dictwrapper
from kitt.decorators import deferredAsThread, debugCall
import config
import sys


#api requirement
SERVICENAME = 'application'
#this will be updated by the service loader and is an API requirement
SERVICECONFIG = dictwrapper({
    'initial_delay': 1.0, #number of seconds to wait on start before scanning
    'recover_interval': 10.0, #number of seconds to wait in between crash searches
    'recovery_period': 60 #number of seconds between recovery attempts
})

log = logWithContext(type=SERVICENAME)
       
from droned.applications import pluginFactory
pluginFactory.loadAppPlugins() #get all the app plugins ready to be used

class ApplicationLoader(Service):
   scanning = defer.succeed(None)
   tracking = set()
   first_run = False

   def _first_scan(self):
       for pid in listProcesses():
           try: AppProcess(Server(config.HOSTNAME), pid)
           except InvalidProcess: pass
  
   def startService(self):
       """Start All AppManager Services"""
       if self.scanning.called: #need to pre-populate values
           self.scanning = defer.maybeDeferred(self._first_scan)
       self.first_run = True
       self._task = task.LoopingCall(self.scan_app_instances)

       #plugins will be created and loaded when needed
       for shortname in config.APPLICATIONS.keys():
           manager = None
           try:
               applog = logWithContext(type=shortname,route=SERVICENAME)
               applog('Loading Application Plugin')
               applog('Creating Application Manager')
               manager = AppManager(shortname)
               manager.parentService = self
               #check and see if the model is bound
               if not AppManager(shortname).running:
                   applog('Starting Application Manager')
                   manager.start()
           except:
               failure = Failure()
               #bad plugin, not adaptable
               failures = (InvalidPlugin, TypeError)
               if failure.check(*failures) and manager:
                   log('plugin for %s is invalid' % (manager.name,))
                   manager.action.__class__.delete(manager.action)
                   try: pluginFactory.delete_plugin(manager.model)
                   except: pass #silence
                   AppManager.delete(manager)
                   if not config.EXCESSIVE_LOGGING: continue #avoid extra logging
               try: failure.raiseException()
               except: crashReport('ApplicationLoader', self)
       Service.startService(self)
       Event('instance-started').subscribe(self.reset_tracking)
       #wire allapps action into the server
       drone.builtins.update({
           'allapps': self.allapps_action,
           'applist': self.applist_action,
       })
       #delay scanning by some interval
       config.reactor.callLater(SERVICECONFIG.initial_delay, self._start_all_tasks)

   def _start_all_tasks(self):
       self._task.start(SERVICECONFIG.recover_interval)

   def scan_app_instances(self):
       """scan for instance anomolies and fire Events as needed"""
       if self.scanning.called:
           need_scan = False
           for am in AppManager.objects:
               if not am.running: continue
               if am.discover:
                   need_scan = True
                   break #an appmanager wan't help
           if not need_scan: return
           self.scanning = self._scan()
       else:
           log('busy scanning from last interation')

   def reset_tracking(self, occurrence):
       """reset tracking criteria when an instance starts"""
       try: self.tracking.discard(occurrence.instance)
       except: pass

#TODO this loop runs hot b/c of IO, but most of the heavy work is in a thread
   @defer.deferredGenerator
   def _scan(self):
       for pid in listProcesses():
           try: AppProcess(Server(config.HOSTNAME), pid)
           except InvalidProcess: pass
           except IOError: pass #happens on linux when a pid dies
           except: err('process table scanning error')
       #scan for crashed instances
       for app in App.objects:
           if not app.__class__.isValid(app): continue
           for ai in app.localappinstances:
               if not ai.__class__.isValid(ai): continue
               if ai in self.tracking: continue
               if not self.first_run: #avoid process table races
                   self.tracking.add(ai)
                   config.reactor.callLater(SERVICECONFIG.recovery_period,
                       self.tracking.discard, ai
                   )
                   if not ai.enabled: continue #skip disabled
               result = None
               if ai.running and not ai.shouldBeRunning:
                   ai.shouldBeRunning = True
               if ai.running: continue
               manager = AppManager(ai.app.name)
               if not manager.running:
                   continue #skip managers that are not running
               if not manager.discover:
                   continue #app manager claims to be ok
               #look for processes that we can assimilate
               d = manager.model.findProcesses()
               wfd = defer.waitForDeferred(d)
               yield wfd
               for (pid, result) in wfd.getResult():
                   d = manager.model.assimilateProcess(result)
                   wfd2 = defer.waitForDeferred(d)
                   yield wfd2
                   ai2 = wfd2.getResult()
                   if ai2 and isinstance(ai2, AppInstance) and ai2 is ai:
                       Event('instance-found').fire(instance=ai)
                       manager.log('Sucessfully assimilated PID %d' % ai2.pid)
               if ai.running: continue #may have assimilated the app
               if not ai.crashed: continue
               if not ai.enabled: continue #disabled instances are not actionable
               if self.first_run: continue #avoid process table races
               Event('instance-crashed').fire(instance=ai)
               #cool off on eventing for a little while
       #keep the process objects up to date
       for process in AppProcess.objects:
           try:
               if not process.localInstall: continue
               if not process.running:
                   AppProcess.delete(process)
           except:
               err('process book keeping error')
       d = defer.Deferred()
       config.reactor.callLater(0.01, d.callback, None)
       wfd = defer.waitForDeferred(d)
       yield wfd
       wfd.getResult()
       self.first_run = False
       yield 'done'

   def stopService(self):
       """Stop All AppManager Services"""
       for x in ['allapps', 'applist']:
           if x in drone.builtins:
               del drone.builtins[x]
       Event('instance-started').unsubscribe(self.reset_tracking)
       for manager in AppManager.objects:
           if manager.running:
               mesg = 'Stopping Application Manager'
               logWithContext(type=manager.name,route=SERVICENAME)(mesg)
               manager.stop()
               #plugins are stateless by design
               pluginFactory.delete_plugin(manager.model)
       if self._task.running: self._task.stop()
       Service.stopService(self)

   #!!!Note docstring is funny for admin usage over blaster
   @defer.deferredGenerator
   def allapps_action(self, argstr):
       """Usage allapps: <method> [args]

  dispatch the same command to all application managers.

    <method>	method to invoke on all appmanagers.
    [args]	optional arguments to pass along.

  examples:

    ''            #shows help documentation for all applications
    'status'      #invoke status assumes there is only one instance
    'status all'  #invoke status on all application instances
    'status 0'    #invoke status on application instance label '0'

  full cli usage:

    $ droneblaster allapps
    $ droneblaster allapps status
    $ droneblaster allapps status all
    $ droneblaster allapps status 0
"""
       result = {}
       descriptions = []
       code = 0
       for obj in AppManager.objects:
           try:
               action = obj.action
               if not action: continue #skip 
               d = action(argstr) #let the AdminAction Processes this
               wfd = defer.waitForDeferred(d)
               yield wfd
               foo = wfd.getResult()
               descriptions.append(foo.get('description','None'))
               code += int(foo.get('code', 0))
           except: pass
       result['description'] = '\n'.join(descriptions)
       if not result['description']:
           result['description'] = 'None'
       result['code'] = code
       yield result

   def applist_action(self, argstr):
       """Usage: applist - lists all managed applications"""
       result = {
           'code': 0,
           'applications': []
       } 
       for am in AppManager.objects:
           if not am.running: continue
           result['applications'].append(am.name)
       result['description'] = '\n'.join(sorted(result['applications']))
       return result
 
# module state globals
parentService = None
service = None


###############################################################################
# API Requirements
###############################################################################
def install(_parentService):
    global parentService
    parentService = _parentService

def start():
    global service
    if not running():
        service = ApplicationLoader()
        service.setName(SERVICENAME)
        service.setServiceParent(parentService)

def stop():
    global service
    if running():
        service.disownServiceParent()
        service.stopService()
        service = None

def running():
    return bool(service) and service.running

from kitt.proc import listProcesses, InvalidProcess
from droned.models.appmgr import AppManager, InvalidPlugin
from droned.models.event import Event
from droned.models.app import App, AppProcess, AppInstance
from droned.models.scab import Scab
from droned.models.server import Server, drone

__all__ = ['install', 'start', 'stop', 'running']
