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
import geojson
import colorsys

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
		self.locations = []
		self.titles = []
		self.icons = []
		self.snippets = []
		self.logger = logging.getLogger("kivy.operator.widgets.map")

	def create_marker(self, **kwargs):
		"""
		Create a custom marker to be displayed on the map. All arguments must be
		specified as key word arguments.

		:param bool draggable: Whether the marker can be moved or not by dragging it.
		:param marker_color: The color to use for the icon. Specified as a name or position on a color wheel.
		:type marker_color: float, int, str
		:param bool move_camera: Move the camera to focus on the position of the new marker.
		:param tuple position: The GPS coordinates of where to place the marker as a latitude and longitude pair.
		:param str snippet: A snippet of text to display when the marker is selected.
		:param str title: The title for the new marker:
		:return: The new marker instance.
		"""
		marker_color = kwargs.pop('marker_color', None)
		if isinstance(marker_color, (float, int)):
			kwargs['icon'] = BitmapDescriptorFactory.defaultMarker(marker_color)
		elif isinstance(marker_color, (str, unicode)):
			kwargs['icon'] = BitmapDescriptorFactory.defaultMarker(getattr(BitmapDescriptorFactory, 'HUE_' + marker_color.upper()))

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
		title = "Marker #{0}".format(len(self.user_markers) + 1)
		marker_color = 'violet'
		snippet = now.strftime("Set at %x %X")
		marker = self.create_marker(
			draggable=False,
			marker_color=marker_color,
			position=latlng,
			snippet=snippet,
			title=title
		)

		self.locations.append([latlng.longitude, latlng.latitude])
		self.titles.append(title)
		self.icons.append(self.color_to_hex(marker_color))
		self.snippets.append(snippet)

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
		data = data.items()
		data = data[1][1]
		for d in data:
			pos = [d['geometry']['coordinates'][1], d['geometry']['coordinates'][0]]
			if "marker-color" in d['properties']:
				color = d['properties']['marker-color']
			else:
				color = "#7F00FF"
			if "title" in d['properties']:
				title = d['properties']['title']
			else:
				title = ""
			if "snippet" in d['properties']:
				snippet = d['properties']['snippet']
			else:
				snippet = ""

			self.locations.append(pos)
			self.titles.append(title)
			self.icons.append(color)
			self.snippets.append(snippet)


			marker = self.create_marker(
				draggable=False,
				marker_color=self.hex_to_hsv(color),
				position=pos,
				snippet=snippet,
				title=title
				)

			self.user_markers.append(marker)

	def save_marker_file(self):
		"""
		opening = {}
		main_set = []
		for marker in self.user_markers:
			entry = {}
			properties = {}
			geometry = {}
			coordinates = []

			geometry['type'] = 'Point'
			geometry['coordinates'] = coordinates
			entry['type'] = 'Feature'
			entry['properties'] = properties
			entry['geometry'] = geometry
			main_set.append(entry)
		opening['type'] = 'FeatureCollection'
		opening['features'] = main_set

		json_filename = 'map_markers.json'
		file_location = '/sdcard/operator/'
		#store = dict(type="FeatureCollection", features=store)
		with open(os.path.join(file_location, json_filename), 'w') as file_h:
			json.dump(opening, file_h, sort_keys=True, indent=2, separators=(',', ': '))
		"""

		features = []
		for (location, color, title, snippet) in zip(self.locations, self.icons, self.titles, self.snippets):
			feature = geojson.Feature(geometry=geojson.Point((location)), properties={'marker-color': self.color_to_hex(color), 'title': title, 'snippet': snippet})
			features.append(feature)
		if features:
			feature_collection = geojson.FeatureCollection(features)
			with open('/sdcard/operator/map_markers.json', 'w') as file_h:
				geojson.dump(feature_collection, file_h)

	def color_to_hex(self, color):
		if color == "azure":
			return "007FFF"
		if color == "violet":
			return "7F00FF"
		else:
			return "7F00FF"

	def hex_to_hsv(self, value):
		value = value.lstrip('#')
		lv = len(value)
		rgb = tuple(int(value[i:i+lv/3], 16) for i in range(0, lv, lv/3))
		hsv = colorsys.rgb_to_hsv(rgb[0], rgb[1], rgb[2])
		hue = hsv[0]*360
		return hue

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
			marker_color='azure',
			position=position,
			title='Current Location'
		)
		self.latitude = position[0]
		self.longitude = position[1]
		if first_location_update:
			self.do_move_to_current_location()
