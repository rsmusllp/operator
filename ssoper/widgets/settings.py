# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

import sys
import ConfigParser as CF

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.settings import SettingsWithSpinner
from kivy.app import App
from kivy.config import ConfigParser

class SettingsWidget(BoxLayout):
	def __init__(self, *args, **kwargs):
		super(SettingsWidget, self).__init__(*args, **kwargs)
		self.orientation = 'vertical'
		config = ConfigParser()
		config.read('data/settings/config.ini')
		self.main_app = App.get_running_app()
		settings = SettingsWithSpinner()
		settings.add_kivy_panel()

		try:
			settings.add_json_panel('XMPP', config, 'data/settings/xmpp.json')
			settings.add_json_panel('Map', config, 'data/settings/map.json')
		except CF.Error:
			#This will get caught later on
			pass

		self.add_widget(settings)
		settings.bind(on_close=lambda x: self.close_button())

	def close_button(self):
		"""
		Overwrites the close button to go back to the main menu.
		"""
		self.main_app.root.do_set_screen(self, 'Menu')
