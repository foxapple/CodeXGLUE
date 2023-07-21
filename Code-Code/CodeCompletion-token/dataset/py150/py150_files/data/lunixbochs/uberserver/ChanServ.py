import time, traceback
from Client import Client

class ChanServ:
	def __init__(self, client, root):
		self.client = client
		self._root = root
	
	def onLogin(self):
		self.client.status = self.client._protocol._calc_status(self.client, 0)
		for channel in self._root.channels.values():
			self.Send('JOIN %s' % str(channel.chan))
	
	def Handle(self, msg):
		try:
			if msg.count(' '):
				cmd, args = msg.split(' ', 1)
				if cmd == 'SAID':
					self.handleSAID(args)
				if cmd == 'SAIDPRIVATE':
					self.handleSAIDPRIVATE(args)
		except:
			self._root.error(traceback.format_exc())
	
	def handleSAID(self, msg):
		chan, user, msg = msg.split(' ',2)
		self.HandleMessage(chan, user, msg)

	def handleSAIDPRIVATE(self, msg):
		user, msg = msg.split(' ', 1)
		self.HandleMessage(None, user, msg)

	def HandleMessage(self, chan, user, msg):
		if msg.startswith('!'):
			msg = msg.lstrip('!')
			if msg.lower() == 'help':
				help = self.Help(user)
				self.Send(['SAYPRIVATE %s %s'%(user, s) for s in help.split('\n')])
			else:
				args = None
				if msg.count(' ') >= 2:	# case cmd blah blah+
					splitmsg = msg.split(' ',2)
					if splitmsg[1].startswith('#'): # case cmd #chan arg+
						cmd, chan, args = splitmsg
						chan = chan.lstrip('#')
					else: # case cmd arg arg+
						cmd, args = msg.split(' ',1)
				elif msg.count(' ') == 1: # case cmd arg
					splitmsg = msg.split(' ')
					if splitmsg[1].startswith('#'): # case cmd #chan
						cmd, chan = splitmsg
						chan = chan.lstrip('#')
					else: # case cmd arg
						cmd, args = splitmsg
				else: # case cmd
					cmd = msg
				if not chan: return
				response = self.HandleCommand(chan, user, cmd, args)
				if response:
					if type(response) in (str, unicode):
						self.Send('SAYPRIVATE %s %s ' % (user, response))
					if type(response) in (list, tuple, set):
						for msg in response:
							self.Send('SAYPRIVATE %s %s'%(user, msg))

	def Help(self, user):
		return 'Hello, %s!\nI am an automated channel service bot,\nfor the full list of commands, see http://springrts.com/dl/ChanServCommands.html\nIf you want to go ahead and register a new channel, please contact one of the server moderators!' % user
	
	def HandleCommand(self, chan, user, cmd, args=None):
		client = self.client._protocol.clientFromUsername(user)
		cmd = cmd.lower()
		
		if chan in self._root.channels:
			channel = self._root.channels[chan]
			access = channel.getAccess(client)
			if cmd == 'info':
				founder = self.client._protocol.clientFromID(channel.owner)
				if founder: founder = 'Founder is <%s>' % founder.username
				else: founder = 'No founder is registered'
				admins = []
				for admin in channel.admins:
					client = self.client._protocol.clientFromID(admin)
					if client: admins.append(client.username)
				users = channel.users
				antispam = 'on' if channel.antispam else 'off'
				if not admins: mods = 'no operators are registered'
				else: mods = '%i registered operator(s) are <%s>' % (len(admins), '>, <'.join(admins))
				if len(users) == 1: users = '1 user is'
				else: users = '%i users are' % len(users)
				return '#%s info: Anti-spam protection is %s. %s, %s. %s currently in the channel.' % (chan, antispam, founder, mods, users)
			elif cmd == 'topic':
				if access in ['mod', 'founder', 'op']:
					args = args or ''
					channel.setTopic(client, args)
					return '#%s: Topic changed' % chan
				else:
					return '#%s: You do not have permission to set the topic' % chan
			elif cmd == 'unregister':
				if access in ['mod', 'founder']:
					channel.owner = ''
					channel.channelMessage('#%s has been unregistered'%chan)
					self.Send('LEAVE %s' % chan)
					return '#%s: Successfully unregistered.' % chan
				else:
					return '#%s: You must contact one of the server moderators or the owner of the channel to unregister a channel' % chan
			elif cmd == 'changefounder':
				if access in ['mod', 'founder']:
					if not args: return '#%s: You must specify a new founder' % chan
					target = self.client._protocol.clientFromUsername(args)
					if not target: return '#%s: cannot assign founder status to a user who does not exist'
					channel.changeFounder(client, target)
					channel.channelMessage('%s Founder has been changed to <%s>' % (chan, args))
					return '#%s: Successfully changed founder to <%s>' % (chan, args)
				else:
					return '#%s: You must contact one of the server moderators or the owner of the channel to change the founder' % chan
			elif cmd == 'spamprotection':
				if access in ['mod', 'founder']:
					if args == 'on':
						channel.antispam = True
						channel.channelMessage('%s Anti-spam protection was enabled by <%s>' % (chan, user))
						return '#%s: Anti-spam protection is on.' % chan
					elif args == 'off':
						channel.antispam = False
						channel.channelMessage('%s Anti-spam protection was disabled by <%s>' % (chan, user))
						return '#%s: Anti-spam protection is off.' % chan
				
				status = 'off'
				if channel.antispam: status = 'on'
				return '#%s: Anti-spam protection is %s' % (chan, status)
			elif cmd == 'op':
				if access in ['mod', 'founder']:
					if not args: return '#%s: You must specify a user to op' % chan
					target = self.client._protocol.clientFromUsername(args)
					if target and channel.isOp(target): return '#%s: <%s> was already an op' % (chan, args)
					channel.opUser(client, target)
				else:
					return '#%s: You do not have permission to op users' % chan
			elif cmd == 'deop':
				if access in ['mod', 'founder']:
					if not args: return '#%s: You must specify a user to deop' % chan
					target = self.client._protocol.clientFromUsername(args)
					if target and not channel.isOp(target): return '#%s: <%s> was not an op' % (chan, args)
					channel.deopUser(client, target)
				else:
					return '#%s: You do not have permission to deop users' % chan
			elif cmd == 'chanmsg':
				if access in ['mod', 'founder', 'op']:
					if not args: return '#%s: You must specify a channel message' % chan
					target = self.client._protocol.clientFromUsername(args)
					if target and channel.isOp(target): args = 'issued by <%s>: %s' % (user, args)
					channel.channelMessage(args)
					return #return '#%s: insert chanmsg here'
				else:
					return '#%s: You do not have permission to issue a channel message' % chan
			elif cmd == 'lock':
				if access in ['mod', 'founder', 'op']:
					if not args: return '#%s: You must specify a channel key to lock a channel' % chan
					channel.setKey(client, args)
					## STUBS ARE BELOW
					return '#%s: Locked' % chan
				else:
					return '#%s: You do not have permission to lock the channel' % chan
			elif cmd == 'unlock':
				if access in ['mod', 'founder', 'op']:
					channel.setKey(client, '*')
					return '#%s: Unlocked' % chan
				else:
					return '#%s: You do not have permission to unlock the channel' % chan
			elif cmd == 'kick':
				if access in ['mod', 'founder', 'op']:
					if not args: return '#%s: You must specify a user to kick from the channel' % chan
					
					if args.count(' '):
						target, reason = args.split(' ', 1)
					else:
						target = args
						reason = None
						
					if target in channel.users:
						target = self.client._protocol.clientFromUsername(target)
						channel.kickUser(client, target, reason)
						return '#%s: <%s> kicked' % (chan, target.username)
					else: return '#%s: <%s> not in channel' % (chan, target)
				else:
					return '#%s: You do not have permission to kick users from the channel' % chan
			elif cmd == 'mute':
				if access in ['mod', 'founder', 'op']:
					if not args: return '#%s: You must specify a user to mute' % chan
					else:
						if args.count(' '): target, duration = args.split(' ', 1)
						else:
							target = args
							duration = -1
					try:
						duration = float(duration)
					except ValueError:
						return '#%s: Duration must be an integer!' % chan
					target = self.client._protocol.clientFromUsername(target)
					channel.muteUser(client, target, duration)
				else:
					return '#%s: You do not have permission to mute users' % chan
			elif cmd == 'unmute':
				if access in ['mod', 'founder', 'op']:
					if not args: return '#%s: You must specify a user to unmute' % chan
					target = self.client._protocol.clientFromUsername(args)
					channel.unmuteUser(client, target)
				else:
					return '#%s: You do not have permission to unmute users' % chan
			elif cmd == 'mutelist':
				if channel.mutelist:
					mutelist = dict(channel.mutelist)
					muted = ['#%s: Mute list (%i entries):  '%(chan, len(mutelist))]
					for user in mutelist:
						m = mutelist[user].copy()
						client = self.client._protocol.clientFromID(user)
						if not client:
							del mutelist[user]
							continue
						message = self.client._protocol._format_time(m['expires']) + (' by IP.' if m['ip'] else '.')
						muted.append('%s, %s' % (client.username, message))
					return muted
				else:
					return '#%s: Mute list is empty!' % chan
		
		if cmd == 'register':
			if client.isMod():
				if not args: args = user
				self.Send('JOIN %s' % chan)
				channel = self._root.channels[chan]
				target = self.client._protocol.clientFromUsername(args)
				if target:
					channel.setFounder(client, target)
					return '#%s: Successfully registered to <%s>' % (chan, args.split(' ',1)[0])
				else:
					return '#%s: User <%s> does not exist.' % (chan, args)
			elif not chan in self._root.channels:
				return '#%s: You must contact one of the server moderators or the owner of the channel to register a channel' % chan
		return ''
	
	def Send(self, msg):
		if type(msg) == list or type(msg) == tuple:
			for s in msg:
				self.client._protocol._handle( self.client, s )
		elif type(msg) == str:
			if '\n' in msg:
				for s in msg.split('\n'):
					self.client._protocol._handle( self.client, s )
			else:
				self.client._protocol._handle( self.client, msg )

class ChanServClient(Client):
	'this object is chanserv implemented through the standard client interface'

	def __init__(self, root, address, session_id):
		'initial setup for the connected client'
		
		Client.__init__(self, root, None, address, session_id)
		
		self.static = True # can't be removed... don't want to anyway :)
		self.logged_in = True
		self.access = 'admin'
		self.accesslevels = ['admin', 'mod', 'user', 'everyone']
		
		self.bot = 1
		self.username = 'ChanServ'
		self.password = 'ChanServ'
		self.cpu = '9001'
		self.lobby_id = 'ChanServ'
		self._root.usernames[self.username] = self
		self._root.console_write('Successfully logged in static user <%s> on session %s.'%(self.username, self.session_id))
		
	def Bind(self, handler=None, protocol=None):
		if handler:
			self.handler = handler
		self.ChanServ = ChanServ(self, self._root)
		if protocol and not self._protocol:
			self._protocol = protocol
			self.ChanServ.onLogin()
		else:
			self._protocol = protocol

	def Handle(self, data):
		pass

	def Remove(self, reason=None):
		pass

	def Send(self, msg):
		self.SendNow(msg)

	def SendNow(self, msg):
		if not msg: return
		self.ChanServ.Handle(msg)

	def FlushBuffer(self):
		pass
