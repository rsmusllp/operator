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
import threading

from android.runnable import run_on_ui_thread
import gmaps
from jnius import autoclass
from kivy.properties import NumericProperty

if sys.version_info >= (3, 0):
	unicode = str

# used for marker icon colors: https://developer.android.com/reference/com/google/android/gms/maps/model/BitmapDescriptorFactory.html
BitmapDescriptorFactory = autoclass('com.google.android.gms.maps.model.BitmapDescriptorFactory')

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
		self.is_ready = False
		self.bind(on_map_click=self.on_map_widget_click, on_ready=self.on_map_widget_ready)
		self._last_known_location_marker = None
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
			self.move_camera(kwargs['position'])
		marker_opts = super(MapWidget, self).create_marker(**kwargs)

		results = []
		completed = threading.Event()
		def _wrapped():
			results.append(self.map.addMarker(marker_opts))
			completed.set()
		wrapped = run_on_ui_thread(_wrapped)
		wrapped()
		completed.wait()
		return results.pop()

	@run_on_ui_thread
	def move_camera(self, position):
		self.map.moveCamera(self.camera_update_factory.newLatLngZoom(position, self.zoom_level))

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
		self.is_ready = True
		self.map.getUiSettings().setZoomControlsEnabled(False)
		self.map.setMapType(MAP_TYPE_HYBRID)
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

	def do_move_to_current_location(self):
		if not self._last_known_location_marker:
			return
		self.move_camera(self.create_latlng(self.latitude, self.longitude))

	def update_location(self, position, altitude=None, bearing=None, speed=None):
		self.logger.info('map received gps location update')
		first_location_update = False
		if self._last_known_location_marker:
			self._last_known_location_marker.remove()
		else:
			first_location_update = True
		self._last_known_location_marker = self.create_marker(
			draggable=False,
			icon_color='azure',
			position=position,
			title='Current Location'
		)
		self.latitude = position[0]
		self.longitude = position[1]
		if first_location_update:
			self.do_move_to_current_location()
