#!/usr/bin/env python

import getpass
import json
import logging
import optparse
import random
import sys
import time

from sleekxmpp import ClientXMPP

# across the street from SecureState
START_COORDINATES = (41.424383, -81.514535)
XMPP_SERVER = ('98.103.103.163', 443)

class OperatorSimulatorBot(ClientXMPP):
	def __init__(self, jid, password):
		super(OperatorSimulatorBot, self).__init__(jid, password)

		self.add_event_handler('session_start', self.start, threaded=True)
		self.add_event_handler('user_location_publish', self.user_location_publish)
		self.add_event_handler('user_mood_publish', self.user_mood_publish)
		self.add_event_handler('ssl_invalid_cert', lambda cert: False)

		self.register_plugin('xep_0004')
		self.register_plugin('xep_0030')
		self.register_plugin('xep_0060')
		self.register_plugin('xep_0080')
		self.register_plugin('xep_0107')
		self.register_plugin('xep_0115')
		self.register_plugin('xep_0128')
		self.register_plugin('xep_0163')

	def start(self, event):
		self.send_presence()
		self.get_roster()
		self['xep_0115'].update_caps()

	def user_location_publish(self, msg):
		geo = msg['pubsub_event']['items']['item']['geoloc']
		print("%s is at:" % msg['from'])
		for key, val in geo.values.items():
			if val:
				print("  %s: %s" % (key, val))

	def user_mood_publish(self, msg):
		mood = msg['pubsub_event']['items']['item']['mood'].values['value']
		print("{0} is feeling {1}".format(str(msg['from']), mood))

if __name__ == '__main__':
	# Setup the command line arguments.
	optp = optparse.OptionParser()

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
	optp.add_option('-j', '--jid', dest='jid', help='JID to use')
	optp.add_option('-p', '--password', dest='password', help='password to use')

	opts, args = optp.parse_args()

	# Setup logging.
	logging.basicConfig(level=opts.loglevel, format='%(levelname)-8s %(message)s')

	if opts.jid is None:
		opts.jid = raw_input('Username: ')
	if opts.password is None:
		opts.password = getpass.getpass('Password: ')

	xmpp = OperatorSimulatorBot(opts.jid, opts.password)
	xmpp.connect(XMPP_SERVER)
	xmpp.process()

	latitude = START_COORDINATES[0]
	longitude = START_COORDINATES[1]
	while True:
		mood = ['angry', 'calm', 'happy'][random.randint(0, 2)]
		xmpp['xep_0107'].publish_mood(value=mood)
		print("published mood update: {0}".format(mood))

		if random.randint(0, 1):
			offset = 0.00005
		else:
			offset = -0.00005
		if random.randint(0, 1):
			latitude += offset
		else:
			longitude += offset
		xmpp['xep_0080'].publish_location(
			lat=latitude,
			lon=longitude
		)
		print("published location update: ({0}, {1})".format(latitude, longitude))
		try:
			time.sleep(20)
		except KeyboardInterrupt:
			break
	print('disconnecting, please wait...')
	xmpp.disconnect()


