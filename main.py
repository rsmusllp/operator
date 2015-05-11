#!/usr/bin/env python

__version__ = '0.1'

import logging
import os
import time

from kivy import platform
from kivy.app import App
from kivy.core.audio import SoundLoader
from kivy.uix.boxlayout import BoxLayout

on_android = False

if platform == 'android':
	from plyer import camera
	on_android = True

class Operator(BoxLayout):
	def __init__(self, *args, **kwargs):
		self.logger = logging.getLogger("kivy.operator.{0}".format(self.__class__.__name__))
		super(Operator, self).__init__(*args, **kwargs)

	def do_play_sound(self, sound_file):
		# load a sound and play it
		sound = SoundLoader.load(sound_file)
		sound.play()

	def do_take_picture(self):
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

class MainApp(App):
	def build(self):
		return Operator()

	def on_pause(self):
		return True

	def on_resume(self):
		pass

if __name__ == '__main__':
	MainApp().run()
