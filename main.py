#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

import logging

from ssoper.widgets.root import RootWidget

from kivy.app import App
from kivy.factory import Factory

Factory.register('MapWidget', module='ssoper.widgets.map')

class MainApp(App):
	def __init__(self, *args, **kwargs):
		super(MainApp, self).__init__(*args, **kwargs)
		self.map = None

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
