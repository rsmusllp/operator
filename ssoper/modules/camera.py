# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

import time

from kivy.clock import mainthread
from kivy import platform
from plyer import camera

@mainthread
def take_picture():
	"""Take a picture with the built in camera and save it to disk."""
	if platform != 'android':
		return
	picture_name = time.strftime('%Y-%m-%d-%H-%M-%S') + '.jpg'
	picture_output = '/storage/sdcard0/' + picture_name
	camera.take_picture(picture_output, lambda file_name: False)
