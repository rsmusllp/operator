# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

import functools
import logging
import colorsys

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, Rectangle
from kivy.uix.settings import SettingsWithSpinner
from kivy.core.window import Window
from kivy.app import App

from plyer import vibrator

from third_party.kivy_toaster.src.toast.androidtoast import toast
from ssoper.utilities.colors import name_to_bg

from kivy.config import ConfigParser

class SettingsWidget(BoxLayout):
	def __init__(self, *args, **kwargs):
		super(SettingsWidget, self).__init__(*args, **kwargs)
		self.orientation = 'vertical'
		#self.master_layout = ScrollView(size_hint=(1, 1))
		#self.master_layout.bind(size=self.master_layout.setter('size'))
		self.message_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
		self.message_layout.bind(minimum_height=self.message_layout.setter('height'))

		config = ConfigParser()
		config.read('data/settings/config.ini')
		self.main_app = App.get_running_app()

		s = SettingsWithSpinner()
		s.add_json_panel('XMPP', config, 'data/settings/xmpp.json')
		s.add_json_panel('Map', config, 'data/settings/map.json')
		self.add_widget(s)
		#self.message_layout.add_widget(s)
		#self.master_layout.add_widget(self.message_layout)
		#self.add_widget(self.message_layout)

		s.bind(on_close=lambda x: self.close_button())

	def close_button(self):
		self.main_app.root.do_set_screen(self, 'Menu')
