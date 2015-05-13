#!/usr/bin/env python

from kivy import platform
from kivy.app import App

import modules.maps
import modules.soundboard

from widgets.toplevel import TopLevel

on_android = False

if platform == 'android':
	from modules.camera import Camera
	on_android = True

class MainApp(App):
	def build(self):
		return TopLevel()

	def on_pause(self):
		return True

	def on_resume(self):
		pass

if __name__ == '__main__':
	MainApp().run()