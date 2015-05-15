#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

import logging
import time

from ssoper.modules.xmpp import OperatorXMPPClient
from ssoper.widgets.root import RootWidget

from kivy.app import App
from kivy.factory import Factory
from plyer import gps

Factory.register('MapWidget', module='ssoper.widgets.map')

GPS_MAX_UPDATE_FREQUENCY = 30
XMPP_SERVER = ('98.103.103.163', 443)
XMPP_USERNAME = ''
XMPP_PASSWORD = ''

class MainApp(App):
	def __init__(self, *args, **kwargs):
		super(MainApp, self).__init__(*args, **kwargs)
		self.logger = logging.getLogger('kivy.operator.app')
		self.map = None
		self.xmpp_client = OperatorXMPPClient(XMPP_SERVER, XMPP_USERNAME, XMPP_PASSWORD)
		self.user_locations = {}
		self._last_location_update = 0

	def build(self):
		self.root = RootWidget()
		self.map = self.root.ids.map_panel_widget.ids.map_widget
		self.xmpp_client.bind(on_user_location_update=self.on_user_location_update)
		gps.configure(on_location=self.on_gps_location)
		gps.start()
		return self.root

	def on_gps_location(self, **kwargs):
		# kwargs on Galaxy S5 contain:
		#   altitude, bearing, lat, lon, speed
		if not ('lat' in kwargs and 'lon' in kwargs):
			return
		current_time = time.time()
		if current_time - self._last_location_update < GPS_MAX_UPDATE_FREQUENCY:
			return
		latitude = kwargs.pop('lat')
		longitude = kwargs.pop('lon')
		altitude = kwargs.pop('altitude', None)
		bearing = kwargs.pop('bearing', None)
		speed = kwargs.pop('speed', None)

		self.map.update_location((latitude, longitude), altitude, bearing, speed)
		self.xmpp_client.update_location((latitude, longitude), altitude, bearing, speed)
		self._last_location_update = current_time

	def on_pause(self):
		return True

	def on_resume(self):
		pass

	def on_stop(self):
		self.xmpp_client.shutdown()

	def on_user_location_update(self, _, info):
		if not self.map.is_ready:
			self.logger.warning('map is not ready for user marker')
			return
		user = info['user']
		if user in self.user_locations:
			self.user_locations[user].remove()
		marker = self.map.create_marker(
			draggable=False,
			title=info['user'],
			position=info['location'],
			icon_color='yellow'
		)
		self.user_locations[user] = marker

if __name__ == '__main__':
	logging.captureWarnings(True)
	MainApp().run()
