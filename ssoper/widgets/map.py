# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

import datetime
import json
import logging
import os
import sys
import time

from android.runnable import run_on_ui_thread
import gmaps
from jnius import autoclass
from kivy.properties import NumericProperty
from plyer import gps

if sys.version_info >= (3, 0):
	unicode = str

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
		self.user_markers = []
		self.logger = logging.getLogger("kivy.operator.widgets.map")

	def create_marker(self, **kwargs):
		icon_color = kwargs.pop('icon_color', None)
		if isinstance(icon_color, (float, int)):
			kwargs['icon'] = BitmapDescriptorFactory.defaultMarker(icon_color)
		elif isinstance(icon_color, (str, unicode)):
			kwargs['icon'] = BitmapDescriptorFactory.defaultMarker(getattr(BitmapDescriptorFactory, 'HUE_' + icon_color.upper()))

		if isinstance(kwargs['position'], (list, tuple)):
			kwargs['position'] = self.create_latlng(kwargs['position'][0], kwargs['position'][1])

		if kwargs.pop('move_camera', False):
			self.map.moveCamera(self.camera_update_factory.newLatLngZoom(kwargs['position'], self.zoom_level))
		marker_opts = super(MapWidget, self).create_marker(**kwargs)
		return self.map.addMarker(marker_opts)

	def on_map_widget_click(self, map_widget, latlng):
		now = datetime.datetime.now()
		marker = self.create_marker(
			draggable=False,
			icon_color='violet',
			position=latlng,
			snippet=now.strftime("Set at %x %X"),
			title="Marker #{0}".format(len(self.user_markers) + 1)
		)
		self.user_markers.append(marker)

	def on_map_widget_ready(self, *args, **kwargs):
		#self.create_marker(title='SecureState', snippet='The mother ship', position=(41.4237737, -81.5143923))
		self.map.getUiSettings().setZoomControlsEnabled(False)
		self.map.setMapType(MAP_TYPE_HYBRID)
		gps.configure(on_location=self.on_gps_location)
		gps.start()
		if os.access('/storage/sdcard0/map_markers.json', os.R_OK):
			self.import_marker_file('/storage/sdcard0/map_markers.json')

	def import_marker_file(self, filename):
		self.logger.info('loading marker file: ' + filename)
		with open(filename, 'r') as file_h:
			data = json.load(file_h)
		for _, details in data.items():
			location = details.pop('location', None)
			if not location:
				continue
			if isinstance(location, (list, tuple)) and len(location) == 2:
				details['position'] = location
			else:
				continue
			details['draggable'] = False
			details['icon_color'] = details.pop('icon_color', 'violet')
			self.create_marker(**details)

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
		if self._last_known_location_marker:
			self._last_known_location_marker.remove()
		self._last_known_location_marker = self.create_marker(
			draggable=False,
			icon_color='azure',
			position=(kwargs['lat'], kwargs['lon']),
			title='Current Location'
		)
		first_location_update = self._last_known_location_update == 0
		self._last_known_location_update = current_time
		self.latitude = kwargs['lat']
		self.longitude = kwargs['lon']
		if first_location_update:
			self.do_move_to_current_location()
