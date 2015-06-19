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
MAP_TYPE_HYBRID = 4
"""Satellite maps with a transparent layer of major streets"""

MAP_TYPE_NONE = 0
"""No base map tiles"""

MAP_TYPE_NORMAL = 1
"""Basic maps"""

MAP_TYPE_SATELLITE = 2
"""Satellite maps with no labels"""

MAP_TYPE_TERRAIN = 3
"""Terrain maps"""

class MapWidget(gmaps.GMap):
	"""
	A Google Maps widget which is used to display geographical information
	including the current users position and custom markers.
	"""
	latitude = NumericProperty()
	longitude = NumericProperty()
	zoom_level = 18
	"""The default level to use for the camera zoom."""
	def __init__(self, *args, **kwargs):
		super(MapWidget, self).__init__(*args, **kwargs)
		self.is_ready = False
		"""Whether the map is ready for drawing or not yet."""
		self.bind(on_map_click=self.on_map_widget_click, on_ready=self.on_map_widget_ready)
		self._last_known_location_marker = None
		self.user_markers = []
		self.logger = logging.getLogger("kivy.operator.widgets.map")

	def create_marker(self, **kwargs):
		"""
		Create a custom marker to be displayed on the map. All arguments must be
		specified as key word arguments.

		:param bool draggable: Whether the marker can be moved or not by dragging it.
		:param icon_color: The color to use for the icon. Specified as a name or position on a color wheel.
		:type icon_color: float, int, str
		:param bool move_camera: Move the camera to focus on the position of the new marker.
		:param tuple position: The GPS coordinates of where to place the marker as a latitude and longitude pair.
		:param str snippet: A snippet of text to display when the marker is selected.
		:param str title: The title for the new marker:
		:return: The new marker instance.
		"""
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
		"""
		Move the camera to focus on a specified position.

		:param position: The position to focus the camera.
		"""
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
		if os.access('/sdcard/operator/map_markers.json', os.R_OK):
			self.import_marker_file('/sdcard/operator/map_markers.json')

	def import_marker_file(self, filename):
		"""
		Import a JSON file describing custom markers that are to be added to the
		map.
		"""
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
		"""
		Update the map marker indicating the current users location.

		:param tuple position: A tuple of the latitude and longitude.
		:param float altitude: The current altitude.
		:param int bearing: The current bearing in degrees East of true North.
		:param int speed: The current speed in meters per second.
		"""
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
