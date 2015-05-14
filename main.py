#!/usr/bin/env python

import logging

from ssoper.widgets.map import MapWidget
from ssoper.widgets.root import RootWidget

from kivy.app import App

class MainApp(App):
	def build(self):
		self.root = RootWidget()
		self.map = self.root.ids.map_panel_widget.ids.map_widget
		return self.root

	def on_pause(self):
		return True

	def on_resume(self):
		pass

if __name__ == '__main__':
	logging.captureWarnings(True)
	MainApp().run()
