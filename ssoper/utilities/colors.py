# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

def name_to_bg(data):
	"""
	Converts a string into a CRC code which is converted into a seemingly random color.

	:param str data: String to convert into a color.
	"""
	is_str = lambda obj: issubclass(obj.__class__, str)
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
	rem = rem/360
	return rem