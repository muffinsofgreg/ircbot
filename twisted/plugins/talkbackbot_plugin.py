from ConfigLParser import ConfigParser

from twisted.application.service import IServiceMaker, Service
from twisted.internet.endpoints import clientFromString
from twisted.plugin import IPlugin
from twisted.python import usage, log
from zope.interface import implementer

from talkback.bot import TalkBackBotFactory
from talkback.quote_picker import QuotePicker


class Options(usage.Options):
    optParameters = [
        ['config', 'c', 'settings.ini', 'Configuration file.'],
    ]


class TalkBackBotService(Service):

    def __init__(self, endpoint, channel, nickname, realname, quotesFilename,
                 triggers):
        self.enpoint = endpoint
        self._channel = channel
        self._nickname = nickname
        self._realname = realname
        self._quotesFilename = quotesFilename
        self._triggers = triggers

    def startService(self):
        """Construct a client & connect to server."""
        from twisted.internet import reactor

        def connected(bot):
            self._bot = bot

        def failure(err):
            log.err(err, _why='Could not connect to specified server.')
            reactor.stop()

        quotes = QuotePicker(self._quotesFilename)
        client = clientFromString(reactor, self._endpoint)
        factory = TalkBackBotFactory(
            self._channel,
            self._nickname,
            self._realname,
            quotes,
            self._triggers,
        )

        return client.connect(factory).addCallbacks(connected, failure)

    def stopService(self):
        """Disconnect"""
        if self.bot and self._bot.transport.connected:
            self._bot.transport.loseConnection()


@implementer(IServiceMaker, IPlugin)
class BotServiceMaker(object):
    tapname = "twsrs"
    description = "IRC bot that provides quotations from notable women"
    options = Options

    def makeService(self, options):
        """Construct the talkbackbot service."""
        # instantiate ConfigParser
        config = ConfigParser()
        # read method reads the options and passes into 'config'
        config.read([options['config']])
        triggers = [
            # strips the triggers and avoids null characters
            trigger.strip()
            for trigger
            # pulls on triggers in the ('talkback', 'triggers' function (see
            # settings.ini
            in config.get('talkback', 'triggers').split('\n')
            if trigger.strip()
        ]

        # instantiates class pulls from config, defined above with configParser
        return TalkBackBotService(
            endpoint=config.get('irc', 'endpoint'),
            channel=config.get('irc', 'channel'),
            nickname=config.get('irc', 'nickname'),
            realname=config.get('irc', 'realname'),
            quotesFilename=config.get('talkback', 'quotesFilename'),
            triggers=triggers,
        )

# Now construct an object which *provides* the relevant interfaces
# The name of this variable is irrelevant, as long as there is *some*
# name bound to a provider of IPlugin and IServiceMaker.


serviceMaker = BotServiceMaker()
