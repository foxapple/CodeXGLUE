#!/usr/bin/python

import os
import traceback

from twisted.words.protocols import irc
from twisted.internet import protocol, ssl
from twisted.application import internet
from twisted.web import resource

from harold.dispatcher import Dispatcher
from harold.plugins.http import ProtectedResource
from harold.plugin import Plugin
from harold.conf import PluginConfig, Option, tup


class IrcConfig(PluginConfig):
    username = Option(str, default=None)
    nick = Option(str)
    password = Option(str, default=None)
    host = Option(str)
    port = Option(int, default=6667)
    use_ssl = Option(bool, default=False)
    channels = Option(tup, default=[])
    userserv_password = Option(str, default=None)
    heartbeat_channel = Option(str)


def who(irc, sender, channel, *args):
    irc.describe(channel, "is a bot. see https://github.com/spladug/harold")


def debug(irc, sender, channel, *args):
    irc.describe(channel, "instance `%s` is up!" % os.environ.get("name", "main"))


class IRCBot(irc.IRCClient):
    realname = "Harold"
    lineRate = 1  # rate limit to 1 message / second
    heartbeatInterval = 30
    maxOutstandingHeartbeats = 3

    def irc_PONG(self, prefix, params):
        print "Received PONG."
        self.outstanding_heartbeats = max(self.outstanding_heartbeats-1, 0)

    def startHeartbeat(self):
        self.outstanding_heartbeats = 0
        irc.IRCClient.startHeartbeat(self)

    def _sendHeartbeat(self):
        if self.outstanding_heartbeats > self.maxOutstandingHeartbeats :
            print "Too many heartbeats missed. Killing connection."
            self.transport.loseConnection()
            return
        else:
            print "Sending PING. %d heartbeats outstanding." % self.outstanding_heartbeats

        irc.IRCClient._sendHeartbeat(self)
        self.outstanding_heartbeats += 1

    def signedOn(self):
        print "Signed on!"

        if self.userserv_password:
            self.msg("userserv", "login %s %s" % (self.username,
                                                  self.userserv_password))

        for channel in self.factory.channels:
            self.join(channel)

        self.factory.dispatcher.registerConsumer(self)

    def connectionLost(self, *args, **kwargs):
        print "Connection lost."
        irc.IRCClient.connectionLost(self, *args, **kwargs)
        self.factory.dispatcher.deregisterConsumer(self)

    def privmsg(self, user, channel, msg):
        sender_nick = user.partition('!')[0]
        self.factory.onMessageReceived(sender_nick, channel, msg)

    def send_message(self, channel, message):
        # get rid of any evil characters that might allow shenanigans
        message = unicode(message)
        message = message.translate({
            ord("\r"): None,
            ord("\n"): None,
        })

        # ensure the message isn't too long
        message = message[:500]

        self.msg(channel, message.encode('utf-8'))

    def set_topic(self, channel, topic):
        self.topic(channel, topic.encode('utf-8'))



class IRCBotFactory(protocol.ClientFactory):
    protocol = IRCBot

    def __init__(self, plugin, config, dispatcher, channels):
        self.plugin = plugin
        self.config = config
        self.dispatcher = dispatcher
        self.channels = channels

    def buildProtocol(self, addr):
        prot = protocol.ClientFactory.buildProtocol(self, addr)
        prot.nickname = self.config.nick
        prot.password = self.config.password
        prot.username = self.config.username
        prot.userserv_password = self.config.userserv_password
        prot.heartbeat_channel = self.config.heartbeat_channel
        return prot

    def clientConnectionFailed(self, connector, reason):
        connector.connect()

    def clientConnectionLost(self, connector, reason):
        connector.connect()

    def onMessageReceived(self, sender_nick, channel, msg):
        self.plugin.onMessageReceived(sender_nick, channel, msg)


class MessageListener(ProtectedResource):
    isLeaf = True

    def __init__(self, http, dispatcher):
        ProtectedResource.__init__(self, http)
        self.dispatcher = dispatcher

    def _handle_request(self, request):
        channel = request.args['channel'][0]
        try:
            message = unicode(request.args['message'][0], 'utf-8')
        except UnicodeDecodeError:
            return
        else:
            self.dispatcher.send_message(channel, message)


class SetTopicListener(ProtectedResource):
    isLeaf = True

    def __init__(self, http, dispatcher):
        ProtectedResource.__init__(self, http)
        self.dispatcher = dispatcher

    def _handle_request(self, request):
        channel = request.args['channel'][0]
        new_topic = unicode(request.args['topic'][0], 'utf-8')
        self.dispatcher.set_topic(channel, new_topic)


class ChannelManager(object):
    def __init__(self, basic_channels, bot):
        self.bot = bot
        self.channels = set(basic_channels)

    def add(self, channel):
        if channel not in self.channels:
            self.channels.add(channel)
            self.bot.join(channel)

    def __iter__(self):
        return self.channels.__iter__()


class IrcPlugin(Plugin):
    def __init__(self):
        self.commands = {}
        super(IrcPlugin, self).__init__()

    def register_command(self, handler):
        self.commands[handler.__name__] = handler

    def onMessageReceived(self, sender_nick, channel, msg):
        split = msg.split()
        if len(split) >= 2:
            highlight = split[0].lower()
        else:
            highlight = ""

        if not highlight.startswith(self.config.nick):
            return

        command, args = (split[1].lower(), split[2:])
        fn = self.commands.get(command)
        if not fn:
            return

        try:
            fn(self.bot, sender_nick, channel, *args)
        except:
            traceback.print_exc()
            self.bot.describe(channel, "just had a hiccup.")


def make_plugin(config, http=None):
    irc_config = IrcConfig(config)
    dispatcher = Dispatcher()
    channel_manager = ChannelManager(irc_config.channels, dispatcher)

    # add the http resources
    if http:
        http.root.putChild('message', MessageListener(http, dispatcher))
        topic_root = resource.Resource()
        http.root.putChild('topic', topic_root)
        topic_root.putChild('set', SetTopicListener(http, dispatcher))

    # configure the default irc commands
    p = IrcPlugin()
    p.register_command(who)
    p.register_command(debug)

    # set up the IRC client
    irc_factory = IRCBotFactory(p, irc_config, dispatcher, channel_manager)
    p.config = irc_config
    p.bot = dispatcher
    p.channels = channel_manager
    if irc_config:
        context_factory = ssl.ClientContextFactory()
        p.add_service(internet.SSLClient(irc_config.host,
                                         irc_config.port,
                                         irc_factory,
                                         context_factory))
    else:
        p.add_service(internet.TCPClient(irc_config.host,
                                         irc_config.port,
                                         irc_factory))
    return p
