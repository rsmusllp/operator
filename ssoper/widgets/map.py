# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

import time

from android.runnable import run_on_ui_thread
import gmaps
from kivy.properties import NumericProperty
from plyer import gps

MAX_LOCATION_REFRESH_FREQUENCY = 30 # seconds

class MapWidget(gmaps.GMap):
	latitude = NumericProperty()
	longitude = NumericProperty()
	zoom_level = 15
	def __init__(self, *args, **kwargs):
		super(MapWidget, self).__init__(*args, **kwargs)
		self.bind(on_ready=self.on_map_widget_ready)
		self._last_known_location_marker = None
		self._last_known_location_update = 0

	def create_marker(self, **kwargs):
		kwargs['position'] = self.create_latlng(kwargs['position'][0], kwargs['position'][1])
		self.map.moveCamera(self.camera_update_factory.newLatLngZoom(kwargs['position'], self.zoom_level))
		marker_opts = super(MapWidget, self).create_marker(**kwargs)
		return self.map.addMarker(marker_opts)

	def on_map_widget_ready(self, *args, **kwargs):
		#self.create_marker(title='SecureState', snippet='The mother ship', position=(41.4237737, -81.5143923))
		self.map.getUiSettings().setZoomControlsEnabled(False)
		gps.configure(on_location=self.on_gps_location)
		gps.start()

	@run_on_ui_thread
	def do_move_to_current_location(self):
		if not self._last_known_location_update:
			return
		position = self.create_latlng(self.latitude, self.longitude)
		self.map.moveCamera(self.camera_update_factory.newLatLngZoom(position, self.zoom_level))

	def on_gps_location(self, **kwargs):
		if not ('lat' in kwargs and 'lon' in kwargs):
			return
		current_time = time.time()
		if current_time - self._last_known_location_update < MAX_LOCATION_REFRESH_FREQUENCY:
			return
		self._last_known_location_update = current_time
		if self._last_known_location_marker:
			self._last_known_location_marker.remove()
		self._last_known_location_marker = self.create_marker(draggable=False, title='Current Location', position=(kwargs['lat'], kwargs['lon']))
		self.latitude = kwargs['lat']
		self.longitude = kwargs['lon']
