# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

import logging

import kivy.event
import sleekxmpp

class RawXMPPClient(sleekxmpp.ClientXMPP):
	def __init__(self, jid, password):
		super(RawXMPPClient, self).__init__(jid, password)
		self.logger = logging.getLogger('kivy.operator.xmpp.raw_client')
		self.add_event_handler('session_start', self._on_session_start, threaded=True)

		self.register_plugin('xep_0004')
		self.register_plugin('xep_0030')
		self.register_plugin('xep_0060')
		self.register_plugin('xep_0080')
		self.register_plugin('xep_0115')
		self.register_plugin('xep_0128')
		self.register_plugin('xep_0163')

	def _on_session_start(self, event):
		self.logger.info('xmpp session started')
		self.send_presence()
		self.get_roster()
		self['xep_0115'].update_caps()

class OperatorXMPPClient(kivy.event.EventDispatcher):
	def __init__(self, server, username, password):
		super(OperatorXMPPClient, self).__init__()
		self.logger = logging.getLogger('kivy.operator.xmpp.client')
		self.register_event_type('on_user_location_update')

		self.jid = "{0}/operator".format(username)
		self._raw_client = RawXMPPClient(self.jid, password)
		self._raw_client.add_event_handler('user_location_publish', self._on_xmpp_user_location_publish)
		if self._raw_client.connect(server):
			self.logger.info("connected to xmpp server {0} {1}:{2}".format(self.jid, server[0], server[1]))
		self._raw_client.process()

	def _on_xmpp_user_location_publish(self, xmpp_msg):
		geo = xmpp_msg['pubsub_event']['items']['item']['geoloc']
		if not ('lat' in geo.values and 'lon' in geo.values):
			self.logger.warning('received user location without lat/lon info')
			return
		info = dict(user=str(xmpp_msg['from']), location=(geo.values['lat'], geo.values['lon']))
		try:
			self.dispatch('on_user_location_update', info)
		except Exception:
			self.logger.error('failed to dispatch the user location update', exc_info=True)

	def on_user_location_update(self, info):
		self.logger.info("user {0} location updated to {1}".format(info['user'], info['location']))

	def shutdown(self):
		self._raw_client.disconnect()
