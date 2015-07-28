# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

import collections
import colorsys

RGBColorTuple = collections.namedtuple('RGBColor', ('red', 'green', 'blue'))

def name_to_bg(data):
	"""
	Converts a string into a CRC code which is converted into a seemingly random color.

	:param str data: String to convert into a color.
	:return: Hue color.
	:rtype: float
	"""
	is_str = lambda obj: issubclass(obj.__class__, str)
	is_bytes = lambda obj: issubclass(obj.__class__, str)
	poly = 0x1021
	reg = 0x0000

	if is_str(data):
		data = list(map(ord, data))
	elif is_bytes(data):
		data = list(data)

	data.append(0)
	data.append(0)

	for byte in data:
		mask = 0x80
		while mask > 0:
			reg <<= 1
			if byte & mask:
				reg += 1
			mask >>= 1
			if reg > 0xffff:
				reg &= 0xffff
				reg ^= poly

	rem = reg % 360
	rem = float(rem)
	rem = rem / 360
	return rem

def hex_to_rgb(color):
	"""
	Converts a hex triplet into an RGB tuple.

	:param str color: The hex code.
	:return: RGB coordinates.
	:rtype: tuple
	"""
	if color.startswith('#'):
		color = color[1:]
	if len(color) != 6:
		raise ValueError('hex color code is in an invalid format')
	rgb = (int(x, 16) for x in (color[i:i + 2] for i in range(0, 6, 2)))
	rgb = RGBColorTuple(*rgb)
	return rgb

def hex_to_hsv(color):
	"""
	Converts a color hex code to a HSV value that can be read by the Google marker API.

	:param str color: The hex code.
	:return: Hue color.
	:rtype: int
	"""
	rgb = hex_to_rgb(color)
	hsv = colorsys.rgb_to_hsv(*rgb)
	hue = hsv[0] * 360
	return hue
