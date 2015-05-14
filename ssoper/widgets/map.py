# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

import datetime
import time

from android.runnable import run_on_ui_thread
import gmaps
from jnius import autoclass
from kivy.properties import NumericProperty
from plyer import gps

# used for marker icon colors: https://developer.android.com/reference/com/google/android/gms/maps/model/BitmapDescriptorFactory.html
BitmapDescriptorFactory = autoclass('com.google.android.gms.maps.model.BitmapDescriptorFactory')

MAX_LOCATION_REFRESH_FREQUENCY = 30 # seconds
# map type constants: https://developer.android.com/reference/com/google/android/gms/maps/GoogleMap.html
MAP_TYPE_HYBRID = 4  # satellite maps with a transparent layer of major streets
MAP_TYPE_NONE = 0  # no base map tiles
MAP_TYPE_NORMAL = 1  # basic maps
MAP_TYPE_SATELLITE = 2  # satellite maps with no labels
MAP_TYPE_TERRAIN = 3  # terrain maps

class MapWidget(gmaps.GMap):
	latitude = NumericProperty()
	longitude = NumericProperty()
	zoom_level = 20
	def __init__(self, *args, **kwargs):
		super(MapWidget, self).__init__(*args, **kwargs)
		self.bind(on_map_click=self.on_map_widget_click, on_ready=self.on_map_widget_ready)
		self._last_known_location_marker = None
		self._last_known_location_update = 0

	def create_marker(self, **kwargs):
		if isinstance(kwargs.get('icon'), (float, int)):
			kwargs['icon'] = BitmapDescriptorFactory.defaultMarker(kwargs['icon'])
		if isinstance(kwargs['position'], tuple):
			kwargs['position'] = self.create_latlng(kwargs['position'][0], kwargs['position'][1])
		self.map.moveCamera(self.camera_update_factory.newLatLngZoom(kwargs['position'], self.zoom_level))
		marker_opts = super(MapWidget, self).create_marker(**kwargs)
		return self.map.addMarker(marker_opts)

	def on_map_widget_click(self, map_widget, latlng):
		now = datetime.datetime.now()
		self.create_marker(
			draggable=False,
			icon=BitmapDescriptorFactory.HUE_VIOLET,
			position=latlng,
			snippet=now.strftime("Set at %x %X"),
			title='Custom Point'
		)

	def on_map_widget_ready(self, *args, **kwargs):
		#self.create_marker(title='SecureState', snippet='The mother ship', position=(41.4237737, -81.5143923))
		self.map.getUiSettings().setZoomControlsEnabled(False)
		self.map.setMapType(MAP_TYPE_HYBRID)
		gps.configure(on_location=self.on_gps_location)
		gps.start()

	@run_on_ui_thread
	def do_cycle_map_type(self):
		map_type = self.map.getMapType()
		# 4 is the highest map type constant
		if map_type == 4:
			# skip map type none
			map_type = MAP_TYPE_NONE
		map_type += 1
		self.map.setMapType(map_type)

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
		self._last_known_location_marker = self.create_marker(
			draggable=False,
			icon=BitmapDescriptorFactory.HUE_AZURE,
			position=(kwargs['lat'], kwargs['lon']),
			title='Current Location'
		)
		self.latitude = kwargs['lat']
		self.longitude = kwargs['lon']
