# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

import logging

import android.runnable
import kivy.event
import sleekxmpp

class RawXMPPClient(sleekxmpp.ClientXMPP):
	"""The raw XMPP connection."""
	def __init__(self, jid, password):
		super(RawXMPPClient, self).__init__(jid, password)
		self.logger = logging.getLogger('kivy.operator.xmpp.raw_client')
		self.add_event_handler('session_start', self._on_session_start, threaded=True)

		self.register_plugin('xep_0004')
		self.register_plugin('xep_0030')
		self.register_plugin('xep_0060')
		self.register_plugin('xep_0080')
		self.register_plugin('xep_0107')
		self.register_plugin('xep_0115')
		self.register_plugin('xep_0128')
		self.register_plugin('xep_0163')

	def _on_session_start(self, event):
		self.logger.info('xmpp session started')
		self.send_presence()
		self.get_roster()
		self['xep_0115'].update_caps()

class OperatorXMPPClient(kivy.event.EventDispatcher):
	"""
	The class which manages the :py:class:`.RawXMPPClient` and provides the XMPP
	API to the rest of the application.
	"""
	def __init__(self, server, username, password):
		"""
		:param tuple server: The server and port to connect to as a tuple.
		:param str username: The username of the jid, including the XMPP domain.
		:param str password: The password to authenticate with.
		"""
		super(OperatorXMPPClient, self).__init__()
		self.logger = logging.getLogger('kivy.operator.xmpp.client')
		self.register_event_type('on_user_location_update')
		self.register_event_type('on_user_mood_update')

		self.jid = username + '/operator'
		self._raw_client = RawXMPPClient(self.jid, password)
		self._raw_client.add_event_handler('user_location_publish', self.on_xmpp_user_location_publish)
		self._raw_client.add_event_handler('user_mood_publish', self.on_xmpp_user_mood_publish)
		if self._raw_client.connect(server):
			self.logger.info("connected to xmpp server {0} {1}:{2}".format(self.jid, server[0], server[1]))
		self._raw_client.process()
		self.user_locations = {}
		"""A dictionary mapping user JIDs to their last published location."""
		self.user_moods = {}
		"""A dictionary mapping user JIDs to their last published mood."""

	def update_location(self, position, altitude=None, bearing=None, speed=None):
		"""
		Publish the current users updated GPS location via XMPP's XEP-0080
		extension. This allows users to know where each other are.

		:param tuple position: A tuple of the latitude and longitude.
		:param float altitude: The current altitude.
		:param int bearing: The current bearing in degrees East of true North.
		:param int speed: The current speed in meters per second.
		"""
		self.logger.info('xmpp received gps location update')
		kwargs = {
			'lat': position[0],
			'lon': position[1]
		}
		if altitude:
			kwargs['alt'] = altitude
		if bearing:
			kwargs['bearing'] = bearing
		if speed:
			kwargs['speed'] = speed
		self._raw_client['xep_0080'].publish_location(**kwargs)

	def update_mood(self, mood):
		"""
		Publish the current users mood as a value to indicate their status using
		XMPP's XEP-0107. This allows users to know each others status.

		:param str mood: One of the three mood constatns of angry, calm or happy.
		"""
		self.logger.info('xmpp received mood update')
		self._raw_client['xep_0107'].publish_mood(value=mood)

	@android.runnable.run_on_ui_thread
	def on_xmpp_user_location_publish(self, xmpp_msg):
		geo = xmpp_msg['pubsub_event']['items']['item']['geoloc']
		if not ('lat' in geo.values and 'lon' in geo.values):
			self.logger.warning('received user location without lat/lon info')
			return
		info = dict(user=str(xmpp_msg['from']), location=(geo.values['lat'], geo.values['lon']))
		try:
			self.dispatch('on_user_location_update', info)
		except Exception:
			self.logger.error('failed to dispatch the user location update', exc_info=True)

	@android.runnable.run_on_ui_thread
	def on_xmpp_user_mood_publish(self, xmpp_msg):
		mood = xmpp_msg['pubsub_event']['items']['item']['mood'].values['value']
		info = dict(user=str(xmpp_msg['from']), mood=mood)
		try:
			self.dispatch('on_user_mood_update', info)
		except Exception:
			self.logger.error('failed to dispatch the user mood update', exc_info=True)

	def on_user_location_update(self, info):
		self.user_locations[info['user']] = info['location']
		self.logger.info("user {0} location updated to {1}".format(info['user'], info['location']))

	def on_user_mood_update(self, info):
		self.user_moods[info['user']] = info['mood']
		self.logger.info("user {0} mood updated to {1}".format(info['user'], info['mood']))

	def shutdown(self):
		"""Perform any necessary clean up actions to close the XMPP connection."""
		self._raw_client.disconnect()
