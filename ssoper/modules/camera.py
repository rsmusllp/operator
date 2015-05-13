# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

import os
import time

from kivy import platform
from plyer import camera

def take_picture():
	# take a picture and save it
	if platform != 'android':
		return
	picture_name = time.strftime('%Y-%m-%d-%H-%M-%S') + '.jpg'
	picture_output = '/storage/sdcard0/' + picture_name
	camera.take_picture(picture_output, os.path.exists(picture_output))
