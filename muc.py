# -*- coding: utf-8 -*-
import sys
import logging
import getpass
from optparse import OptionParser
import sleekxmpp
import requests
import urllib.request
import io
import json
#from helpers import utf8text
from lxml import html


if sys.version_info < (3, 0):
    from sleekxmpp.util.misc_ops import setdefaultencoding
    setdefaultencoding('utf8')
else:
    raw_input = input

def utf8text(text):
    return text.encode('raw_unicode_escape').decode('utf-8')

class MUCBot(sleekxmpp.ClientXMPP):
    
    week_number = 0
    lastWeek = "0"
    url = 'http://hador.syntronic.se/cgi-bin/tallriksskrapan.py'

    
    def lunch(self, args):
        parse_vecka()
        print("\n" +
        parse_teknikparken() + "\n" +
        parse_kompassen() + "\n" +
        parse_gs()+ "\n" +
        parse_gustafsbro() + "\n" +
        parse_koket() + "\n" +
        parse_kryddan())

    def get_Resturants(self):
        req = requests.get(self.url + '?command=restuaranger')
        obj = json.loads(req.text)
        retval = ''.join('\n {0:20} - {1}'.format(rest['restuarang'], rest['text']) for rest in obj['restuaranger'])
        return retval
    
    def get_Meny(self, resturant, day) :
        urlFull = self.url + '?command=menu'
        if resturant  and resturant != "all":
            urlFull = urlFull + '&resturant=' + resturant
        urlFull += '&dag=' + day
        req = requests.get(urlFull)
        obj = json.loads(req.text)
        retval = 'Vecka: ' + obj['vecka'] + ' dag: ' + obj['dag'] + '\n'
        retval += ''.join('\n {0:10}: {1}'.format(rest['restuarang'], rest['meny']) for rest in obj['restuaranger'])
        return retval

    def get_Help(self) :
        retval = "\n\nSSIBot kan vara till hjälp åt vilsna själar\n"
        retval += "Kommandon:\n"
        retval += "ssibot\t\t\t\t\t\t\tVisar tillgängliga resturanger på tallriksskarpan\n"
        retval += "ssibot all\t\t\t\t\t\t\tVisar alla resturangers meny för fredag\n"
        retval += "ssibot <all> <veckodag>\t\t\t\tVisar alla resturangers meny för <veckodag>\n"
        retval += "ssibot <resturangnamn>\t\t\t\tVisar <resturangnamn> meny på fredag\n"
        retval += "ssibot <veckodag> <resturangnamn>\tVisar <resturangnamn> meny på <veckodag>\n"
        retval += "ssibot help\t\t\t\t\t\tVisar denna hjälp\n\n"
        return retval



    """
    A simple SleekXMPP bot that will greets those
    who enter the room, and acknowledge any messages
    that mentions the bot's nickname.
    """

    def __init__(self, jid, password, room, nick):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        self.room = room
        self.nick = nick

        # The session_start event will be triggered when
        # the bot establishes its connection with the server
        # and the XML streams are ready for use. We want to
        # listen for this event so that we we can initialize
        # our roster.
        self.add_event_handler("session_start", self.start)

        # The groupchat_message event is triggered whenever a message
        # stanza is received from any chat room. If you also also
        # register a handler for the 'message' event, MUC messages
        # will be processed by both handlers.
        self.add_event_handler("groupchat_message", self.muc_message)

        # The groupchat_presence event is triggered whenever a
        # presence stanza is received from any chat room, including
        # any presences you send yourself. To limit event handling
        # to a single room, use the events muc::room@server::presence,
        # muc::room@server::got_online, or muc::room@server::got_offline.
        self.add_event_handler("muc::%s::got_online" % self.room,
                               self.muc_online)


    def start(self, event):
        """
        Process the session_start event.

        Typical actions for the session_start event are
        requesting the roster and broadcasting an initial
        presence stanza.

        Arguments:
            event -- An empty dictionary. The session_start
                     event does not provide any additional
                     data.
        """
        self.get_roster()
        self.send_presence()
        self.plugin['xep_0045'].joinMUC(self.room,
                                        self.nick,
                                        # If a room password is needed, use:
                                        # password=the_room_password,
                                        wait=True)

    def muc_message(self, msg):
        """
        Process incoming message stanzas from any chat room. Be aware
        that if you also have any handlers for the 'message' event,
        message stanzas may be processed by both handlers, so check
        the 'type' attribute when using a 'message' event handler.

        Whenever the bot's nickname is mentioned, respond to
        the message.

        IMPORTANT: Always check that a message is not from yourself,
                   otherwise you will create an infinite loop responding
                   to your own messages.

        This handler will reply to messages that mention
        the bot's nickname.

        Arguments:
            msg -- The received message stanza. See the documentation
                   for stanza objects and the Message stanza to see
                   how it may be used.
        """
        
        daysOfWeek = ['måndag', 'tisdag', 'onsdag', 'torsdag', 'fredag']
        if msg['mucnick'] != self.nick and self.nick in msg['body'].split(" ")[0]:
            mess = msg['body'].split(" ")
            if(len(mess) > 1):
                if (mess[1] == "help"):
                    response = self.get_Help()
                else:
                    day = "fredag"
                    rest = "all"
                    dayInMess = False
                    if any(mess[1] in d for d in daysOfWeek) :
                        dayInMess = True
                        day = mess[1]
                    else :
                        rest = mess[1]

                    if (len(mess) > 2) :
                        if not dayInMess and any(mess[2] in d for d in daysOfWeek) :
                            day = mess[2]
                        else :
                            rest = mess[2]

                    response = self.get_Meny(rest, day)
            else:
                response = "Avaliable Restaurants: \n"+ self.get_Resturants()
                
            self.send_message(mto=msg['from'].bare, mbody=response, mtype='groupchat')

    def muc_online(self, presence):
        """
        Process a presence stanza from a chat room. In this case,
        presences from users that have just come online are
        handled by sending a welcome message that includes
        the user's nickname and role in the room.

        Arguments:
            presence -- The received presence stanza. See the
                        documentation for the Presence stanza
                        to see how else it may be used.
        """
        if (1 == 2) and presence['muc']['nick'] != self.nick:
            self.send_message(mto=presence['from'].bare,
                              mbody="Hello, %s %s" % (presence['muc']['role'],
                                                      presence['muc']['nick']),
                              mtype='groupchat')


if __name__ == '__main__':
    # Setup the command line arguments.
    optp = OptionParser()

    # Output verbosity options.
    optp.add_option('-q', '--quiet', help='set logging to ERROR',
                    action='store_const', dest='loglevel',
                    const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d', '--debug', help='set logging to DEBUG',
                    action='store_const', dest='loglevel',
                    const=logging.DEBUG, default=logging.INFO)
    optp.add_option('-v', '--verbose', help='set logging to COMM',
                    action='store_const', dest='loglevel',
                    const=5, default=logging.INFO)

    # JID and password options.
    optp.add_option("-j", "--jid", dest="jid",
                    help="JID to use")
    optp.add_option("-p", "--password", dest="password",
                    help="password to use")
    optp.add_option("-r", "--room", dest="room",
                    help="MUC room to join")
    optp.add_option("-n", "--nick", dest="nick",
                    help="MUC nickname")

    opts, args = optp.parse_args()

    # Setup logging.
    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')

    if opts.jid is None:
        opts.jid = raw_input("Username: ")
    if opts.password is None:
        opts.password = getpass.getpass("Password: ")
    if opts.room is None:
        opts.room = raw_input("MUC room: ")
    if opts.nick is None:
        opts.nick = raw_input("MUC nickname: ")

    # Setup the MUCBot and register plugins. Note that while plugins may
    # have interdependencies, the order in which you register them does
    # not matter.
    xmpp = MUCBot(opts.jid, opts.password, opts.room, opts.nick)
    xmpp['feature_mechanisms'].unencrypted_plain = True
    xmpp.register_plugin('xep_0030') # Service Discovery
    xmpp.register_plugin('xep_0045') # Multi-User Chat
    xmpp.register_plugin('xep_0199') # XMPP Ping
    
    # Connect to the XMPP server and start processing XMPP stanzas.
    if xmpp.connect(('hador.syntronic.se', 5222), reattempt=True):  #, use_tls=True, use_ssl=False):
        # If you do not have the dnspython library installed, you will need
        # to manually specify the name of the server if it does not match
        # the one in the JID. For example, to use Google Talk you would
        # need to use:
        #
        # if xmpp.connect(('talk.google.com', 5222)):
        #     ...
        xmpp.process(block=True)
        print("Done")
    else:
        print("Unable to connect.")    

    
