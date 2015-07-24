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
import collections

from android.runnable import run_on_ui_thread
import gmaps
from jnius import autoclass
from kivy.properties import NumericProperty

import ssoper.utilities.colors as util_colors

if sys.version_info >= (3, 0):
	unicode = str

BitmapDescriptorFactory = autoclass('com.google.android.gms.maps.model.BitmapDescriptorFactory')
Polyline = autoclass('com.google.android.gms.maps.model.Polyline')
PolylineOptions = autoclass('com.google.android.gms.maps.model.PolylineOptions')
Color = autoclass('android.graphics.Color')

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

MAP_MARKER_FILE = '/sdcard/operator/map_markers.geojson'
Marker = collections.namedtuple('Marker', ['geojson_feature', 'map_object'])
color_dict = {
	'azure': '#007FFF',
	'blue': '#0000FF',
	'cyan': '#00FFFF',
	'green': '#00FF00',
	'magenta': '#FF00FF',
	'orange': '#FF7F00',
	'red': '#FF0000',
	'rose': '#FF007F',
	'violet': '#7F00FF',
	'yellow': '#FFFF00'}

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
		:param marker_color: The color to use for the icon.
			Specified as a name or position on a color wheel.
		:type marker_color: float, int, str
		:param bool move_camera: Move the camera to focus on the position of the new marker.
		:param tuple position: The GPS coordinates of where to place the marker as a latitude
			and longitude pair.
		:param str snippet: A snippet of text to display when the marker is selected.
		:param str title: The title for the new marker:
		:return: The new marker instance.
		"""
		BitmapDescriptorFactory = autoclass('com.google.android.gms.maps.model.BitmapDescriptorFactory')
		marker_color = kwargs.pop('marker_color', None)
		if isinstance(marker_color, (float, int)):
			kwargs['icon'] = BitmapDescriptorFactory.defaultMarker(marker_color)
		elif isinstance(marker_color, (str, unicode)):
			if marker_color.startswith('#'):
				marker_color = util_colors.hex_to_hsv(marker_color)
			else:
				marker_color = getattr(BitmapDescriptorFactory, 'HUE_' + marker_color.upper())
			kwargs['icon'] = BitmapDescriptorFactory.defaultMarker(marker_color)

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
		"""
		Gets called when the user touches the map, indicating they want to create a marker.

		:param map_widget: The current map widget.
		:param latlng: Coordinates of the click.
		"""
		now = datetime.datetime.now()
		title = "Marker #{0}".format(len(self.user_markers) + 1)
		marker_color = 'violet'
		snippet = now.strftime("Set at %x %X")
		feature = geojson.Feature(
			geometry=geojson.Point((latlng.longitude, latlng.latitude)),
			properties={
				'marker-color': Color_dict.get(marker_color, '#7F00FF'),
				'title': title,
				'snippet': snippet
			}
		)
		marker_value = Marker(
			geojson_feature=feature,
			map_object=self.create_marker(
				draggable=False,
				marker_color=Color_dict.get(marker_color, '#7F00FF'),
				position=latlng,
				snippet=snippet,
				title=title
			)
		)
		self.user_markers.append(marker_value)

	def on_map_widget_ready(self, *args, **kwargs):
		"""
		When the map loads, the framework to load a marker file is implemented.
		"""
		self.is_ready = True
		self.map.getUiSettings().setZoomControlsEnabled(False)
		self.map.setMapType(MAP_TYPE_HYBRID)
		if os.access(MAP_MARKER_FILE, os.R_OK):
			self.import_marker_file(MAP_MARKER_FILE)

	def import_marker_file(self, filename):
		"""
		Import a JSON file describing custom markers that are to be added to the
		map.

		:param str filename: Location of the marker JSON.
		"""
		self.logger.info('loading marker file: ' + filename)

		with open(filename, 'r') as file_h:
			data = json.load(file_h)

		for feature in data.get('features', []):
			geometry = feature.get('geometry')
			if not geometry:
				continue
			if geometry.get('type') == 'Point':
				marker_value = Marker(
					geojson_feature=feature,
					map_object=self.create_marker(
						draggable=False,
						marker_color=feature['properties'].get('marker-color', 'violet'),
						position=(geometry['coordinates'][1], geometry['coordinates'][0]),
						snippet=feature['properties'].get('snippet'),
						title=feature['properties'].get('title', 'Unknown Marker')
					)
				)
				self.user_markers.append(marker_value)
			elif geometry.get('type') in ('Polygon', 'LineString'):
				coords = []
				for coord in geometry['coordinates']:
					coords.append(coord)
				marker_value = Marker(
					geojson_feature=feature,
					map_object=self.draw_line(
						coordinates=coords,
						stroke=feature['properties'].get('stroke', Color.BLACK),
						stroke_width=feature['properties'].get('stroke-width', 5)
					)
				)
				self.user_markers.append(marker_value)

	def draw_line(self, coordinates, stroke, stroke_width):
		"""
		Creates a polygon/line based on GeoJson data.

		:param tuple coordinates: The coordinates of all the line vertices necessary in constructing
		the shape.
		:param str stroke: The color of the lines.
		:param int stroke_width: The width of the lines.
		:return: The new polygon/line instance.
		"""
		def _wrapped():
			results.append(self.map.addPolyline(line_opts))
			completed.set()

		if stroke != Color.BLACK:
			stroke = util_colors.hex_to_rgb(stroke)
			stroke = Color.rgb(stroke.red, stroke.green, stroke.blue)
		line_opts = PolylineOptions()

		if len(coordinates)>1:
			for coord in coordinates:
				line_opts.add(self.create_latlng(float(coord[1]), float(coord[0])))
		else:
			for coord in coordinates[0]:
				line_opts.add(self.create_latlng(float(coord[1]), float(coord[0])))

		line_opts.width(stroke_width)
		line_opts.color(stroke)
		results = []
		completed = threading.Event()
		wrapped = run_on_ui_thread(_wrapped)
		wrapped()
		completed.wait()
		return results.pop()

	def save_marker_file(self):
		"""
		Saves the current map marker schema to a GeoJson file.
		"""
		features = []
		for marker in self.user_markers:
			features.append(marker.geojson_feature)
		if not features:
			self.logger.info('no map markers to save')
			return
		feature_collection = geojson.FeatureCollection(features)
		with open(MAP_MARKER_FILE, 'w') as file_h:
			geojson.dump(feature_collection, file_h)
		self.logger.info('saved map markers')

	@run_on_ui_thread
	def do_cycle_map_type(self):
		"""
		Changes map type between satellite and basic.
		"""
		map_type = self.map.getMapType()
		# 4 is the highest map type constant
		if map_type == 4:
			# skip map type none
			map_type = MAP_TYPE_NONE
		map_type += 1
		self.map.setMapType(map_type)

	def do_move_to_current_location(self):
		"""
		Moves the camera to the current location.
		"""
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
