#!/usr/bin/env python

import logging

from ssoper.widgets.map import Map
from ssoper.widgets.toplevel import TopLevel

from kivy.app import App

class MainApp(App):
	def build(self):
		return TopLevel()

	def on_pause(self):
		return True

	def on_resume(self):
		pass

if __name__ == '__main__':
	logging.captureWarnings(True)
	MainApp().run()
