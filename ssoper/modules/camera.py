#!/usr/bin/env python

import os
import time

from plyer import camera

class Camera():
	@staticmethod
	def do_take_picture():
		# take a picture and save it
		if not on_android:
			self.logger.warning('Camera is not implemented on this platform')
			return
		picture_name = time.strftime('%Y-%m-%d-%H-%M-%S') + '.jpg'
		picture_output = '/storage/sdcard0/' + picture_name
		camera.take_picture(picture_output, self.verify_image_saved(picture_output))

	def verify_image_saved(self, file_name):
		# check that the image was saved correctly
		return os.path.exists(file_name)

