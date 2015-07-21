# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

import logging
import threading

import android.runnable
import kivy.event
import sleekxmpp

from sleekxmpp.exceptions import IqError, IqTimeout

from third_party.kivy_toaster.src.toast.androidtoast import toast

class RawXMPPClient(sleekxmpp.ClientXMPP):
	"""The raw XMPP connection."""
	def __init__(self, jid, password, room, nick):
		super(RawXMPPClient, self).__init__(jid, password)
		self.logger = logging.getLogger('kivy.operator.xmpp.raw_client')
		self.add_event_handler('session_start', self._on_session_start, threaded=True)

		self.register_plugin('xep_0004')
		self.register_plugin('xep_0045')
		self.register_plugin('xep_0030')
		self.register_plugin('xep_0060')
		self.register_plugin('xep_0080')
		self.register_plugin('xep_0107')
		self.register_plugin('xep_0115')
		self.register_plugin('xep_0128')
		self.register_plugin('xep_0163')
		self.register_plugin('xep_0199')

		self.room = room
		self.nick = nick

	def _on_session_start(self, event):
		self.logger.info('xmpp session started')
		self.send_presence()
		self.get_roster()
		self['xep_0115'].update_caps()
		self['xep_0045'].joinMUC(
			self.room,
			self.nick,
			pfrom=self.jid,
			wait=True
		)
		self['xep_0045'].configureRoom(self.room, ifrom=self.jid)


class OperatorXMPPClient(kivy.event.EventDispatcher):
	"""
	The class which manages the :py:class:`.RawXMPPClient` and provides the XMPP
	API to the rest of the application.
	"""
	def __init__(self, server, username, password, room, filterB):
		"""
		:param tuple server: The server and port to connect to as a tuple.
		:param str username: The username of the jid, including the XMPP domain.
		:param str password: The password to authenticate with.
		"""
		super(OperatorXMPPClient, self).__init__()
		self.logger = logging.getLogger('kivy.operator.xmpp.client')
		self.register_event_type('on_user_location_update')
		self.register_event_type('on_user_mood_update')
		self.register_event_type('on_message_receive')
		self.register_event_type('on_muc_receive')

		self.room = room
		self.filter = filterB
		self.username = username

		self.messages = []

		self.jid = username + '/operator'
		self.nick = username.split('@')[0]

		self._raw_client = RawXMPPClient(self.jid, password, self.room, self.nick)
		self._raw_client.add_event_handler('user_location_publish', self.on_xmpp_user_location_publish)
		self._raw_client.add_event_handler('user_mood_publish', self.on_xmpp_user_mood_publish)
		self._raw_client.add_event_handler('message', self.on_xmpp_message_receive)
		self._raw_client.add_event_handler("muc::%s::got_online" % self.room, self.muc_online)
		self._raw_client.add_event_handler("groupchat_message", self.on_xmpp_muc_receive)
		self._raw_client.add_event_handler("changed_status", self.wait_for_presences)

		if self._raw_client.connect(server):
			self.logger.info("connected to xmpp server {0} {1}:{2}".format(self.jid, server[0], server[1]))
		self._raw_client.process()
		self.user_locations = {}
		self.user_moods = {}
		self.users = []

		self.received = set()
		self.presences_received = threading.Event()

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

	def get_users(self):
		"""
		Get the roster from the XMPP object.
		"""
		names = []

		try:
			self._raw_client.get_roster()
		except IqError as err:
			self.logger.error('Error: %s' % err.iq['error']['condition'], exc_info=True)
		except IqTimeout:
			self.logger.error('Error: Request timed out', exc_info=True)
		self._raw_client.send_presence()

		self.presences_received.wait(5)

		groups = self._raw_client.client_roster.groups()
		for group in groups:
			for jid in groups[group]:
				connections = self._raw_client.client_roster.presence(jid)
				if connections.items():
					if jid != self.username:
						if self.filter:
							for res in connections.items():
								if res == 'operator':
									names.append(str(jid))			
						else:
							names.append(str(jid))

		self.users = names
		return names

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

	@android.runnable.run_on_ui_thread
	def on_xmpp_message_receive(self, xmpp_msg):
		if xmpp_msg['type'] in ('chat', 'normal'):
			try:
				self.dispatch('on_message_receive', xmpp_msg)
			except Exception:
				self.logger.error('failed to dispatch the message update', exc_info=True)

	@android.runnable.run_on_ui_thread
	def on_xmpp_muc_receive(self, xmpp_msg):
		if xmpp_msg['mucnick'] != self.nick and xmpp_msg['type'] in 'groupchat':
			try:
				self.dispatch('on_muc_receive', xmpp_msg)
			except Exception:
				self.logger.error('failed to dispatch the muc update', exc_info=True)

	def on_message_receive(self, info):
		"""
		Handles when XMPP receives a message. Empty function that is overriden by children.

		:param Message info: The message object handled by XMPP.
		"""
		self.messages.append(info)

	def on_message_send(self, msg, user):
		"""
		Sends the message with the XMPP client handler.

		:param str msg: The body of the message to send.
		:param str user: The user to send the message to.
		"""
		self.logger.info("sending message to " + str(user))
		self._raw_client.send_message(mto=str(user), mbody=msg, mtype='chat')

	def on_muc_receive(self, msg):
		"""
		Handles when XMPP receives a groupmessage. Empty function that is overriden by children.

		:param Message msg: The message object handled by XMPP.
		"""
		pass

	def on_muc_send(self, msg, group):
		"""
		Sends the message with the XMPP client handler.

		:param str msg: The body of the message to send.
		:param str group: The group to send the message to.
		"""
		self.logger.info("sending group message to " + str(group))
		self._raw_client.send_message(mto=group, mbody=msg, mtype='groupchat')

	def on_user_location_update(self, info):
		"""
		Updates the location.

		:param info: The XMPP data object.
		"""
		self.user_locations[info['user']] = info['location']
		self.logger.info("user {0} location updated to {1}".format(info['user'], info['location']))

	def on_user_mood_update(self, info):
		"""
		Updates the mood.

		:param info: The XMPP data object.
		"""
		self.user_moods[info['user']] = info['mood']
		self.logger.info("user {0} mood updated to {1}".format(info['user'], info['mood']))

	def shutdown(self):
		"""
		Perform any necessary clean up actions to close the XMPP connection.
		"""
		self._raw_client.disconnect()

	def muc_online(self, presence):
		"""
		Toasts the user whenever another operator comes online.
		"""
		if presence['muc']['nick'] != self.nick:
			toast(presence['muc']['nick'] + " has come online", True)

	def wait_for_presences(self, pres):
		"""
		Track how many roster entries have received presence updates.
		"""
		self.received.add(pres['from'].bare)
		if len(self.received) >= len(self.client_roster.keys()):
			self.presences_received.set()
		else:
			self.presences_received.clear()
