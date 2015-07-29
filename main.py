#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

import logging
import os
import time
import sys
import threading
import ConfigParser as CF

from ssoper.modules.xmpp import OperatorXMPPClient
from ssoper.widgets.root import RootWidget

from kivy.app import App
from kivy.factory import Factory
from kivy.core.window import Window
from kivy.config import ConfigParser
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup

from plyer import gps
from jnius import autoclass
from smoke_zephyr import utilities as sz_utils

from android.runnable import run_on_ui_thread

Factory.register('MapWidget', module='ssoper.widgets.map')
Factory.register('ChecklistWidget', module='ssoper.widgets.checklist')
Factory.register('FileWidget', module='ssoper.widgets.fileselect')
Factory.register('NotesWidget', module='ssoper.widgets.notes')
Factory.register('SoundboardWidget', module='ssoper.widgets.soundboard')
Factory.register('RecorderWidget', module='ssoper.widgets.recorder')
Factory.register('Toast', module='third_party.kivy_toaster.src.main')
Factory.register('MessageWidget', module='ssoper.widgets.messaging')
Factory.register('SettingsWidget', module='ssoper.widgets.settings')
Factory.register('MenuWidget', module='ssoper.widgets.menu')

PythonActivity = autoclass('org.renpy.android.PythonActivity')
Params = autoclass('android.view.WindowManager$LayoutParams')

class MainApp(App):
	def __init__(self, *args, **kwargs):
		super(MainApp, self).__init__(*args, **kwargs)
		self.logger = logging.getLogger('kivy.operator.app')
		if not os.path.isdir("/sdcard/operator"):
			os.makedirs("/sdcard/operator")
		self.configuration = ConfigParser()
		self.map = None
		self.messaging = None
		self.xmpp_client = None
		self.is_broken = False
		self.user_location_markers = {}
		self._last_location_update = 0
		Window.bind(on_keyboard=self.on_back_btn)
		self.android_setflag()
		self.start = True

	def root_is_ready(self):
		self.config_check()

	def config_check(self):
		self.logger.info("Checking validity of config file")
		try:
			self.configuration.read('data/settings/config.ini')
			self.configuration.get('xmpp', 'server')
			self.configuration.get('xmpp', 'username')
			self.configuration.get('xmpp', 'password')
			self.configuration.get('xmpp', 'room')
			self.configuration.getboolean('xmpp', 'filter')
			self.configuration.getboolean('xmpp', 'toast_all')
			self.config_ok.set()
			self.logger.info("Config file is valid")
		except CF.Error:
			self.is_broken = True
			self.error_dialogue(sys.exc_info())

	def build(self):
		self.root = RootWidget()
		self.map = self.root.ids.map_panel_widget.ids.map_widget
		self.messaging = self.root.ids.message_menu
		try:
			self.xmpp_client = OperatorXMPPClient(
				sz_utils.parse_server(self.configuration.get('xmpp', 'server'), 5222),
				self.configuration.get('xmpp', 'username'),
				self.configuration.get('xmpp', 'password'),
				self.configuration.get('xmpp', 'room'),
				self.configuration.getboolean('xmpp', 'filter')
			)
			self.xmpp_client.bind(on_user_location_update=self.on_user_location_update)
			self.xmpp_client.bind(on_message_receive=self.on_message_receive)
			self.xmpp_client.bind(on_muc_receive=self.on_muc_receive)
			gps.configure(on_location=self.on_gps_location)
			gps.start()
			return self.root
		except CF.Error:
			#This will be caught later on
			pass

	def on_back_btn(self, window, key, *args):
		""" To be called whenever user presses Back/Esc Key """
		# If user presses Back/Esc Key
		if key == 27:
			return self.root.on_back_btn()
		return False

	def build_config(self, config):
		# add default sections here
		default_sections = ('miscellaneous', 'xmpp')
		for section in default_sections:
			if not config.has_section:
				config.add_section(section)

		# load the custom configuration ini file
		custom_config = 'data/settings/config.ini'
		if os.path.isfile(custom_config):
			self.logger.info('loading custom config: {0}'.format(custom_config))
			config.update_config(custom_config, overwrite=False)

	def build_settings(self, settings):
		try:
			settings.add_json_panel('XMPP', self.configuration, 'data/settings/xmpp.json')
			settings.add_json_panel('Map', self.configuration, 'data/settings/map.json')
		except CF.Error:
			#This wil be caught later on
			pass

	def on_message_receive(self, event, msg):
		self.messaging.on_message_receive(msg)

	def on_muc_receive(self, event, msg):
		self.messaging.on_muc_receive(msg)

	def on_gps_location(self, **kwargs):
		# kwargs on Galaxy S5 contain:
		#   altitude, bearing, lat, lon, speed
		if self.start:
			self.messaging.get_users()
			self.start = False
		if not ('lat' in kwargs and 'lon' in kwargs):
			return
		current_time = time.time()
		if current_time - self._last_location_update < self.configuration.getint('miscellaneous', 'gps_update_freq'):
			return
		latitude = kwargs.pop('lat')
		longitude = kwargs.pop('lon')
		altitude = kwargs.pop('altitude', None)
		bearing = kwargs.pop('bearing', None)
		speed = kwargs.pop('speed', None)

		self.map.update_location((latitude, longitude), altitude, bearing, speed)
		self.xmpp_client.update_location((latitude, longitude), altitude, bearing, speed)
		self._last_location_update = current_time

	def get_users(self):
		return self.xmpp_client.get_users()

	def send_message(self, msg, user):
		self.xmpp_client.on_message_send(msg, user)

	def send_muc(self, msg, group):
		self.xmpp_client.on_muc_send(msg, group)

	def on_pause(self):
		return False

	def on_resume(self):
		pass

	def on_stop(self):
		if not self.is_broken:
			self.map.save_marker_file()
			self.xmpp_client.shutdown()

	def on_user_location_update(self, _, info):
		if not self.map.is_ready:
			self.logger.warning('map is not ready for user marker')
			return
		user = info['user']
		if user in self.user_location_markers:
			self.user_location_markers[user].remove()
		user_mood = self.xmpp_client.user_moods.get(user, 'calm')
		icon_color = {'angry': 'red', 'calm': 'yellow', 'happy': 'green'}.get(user_mood, 'yellow')
		marker = self.map.create_marker(
			draggable=False,
			title=info['user'],
			position=info['location'],
			marker_color=icon_color
		)
		self.user_location_markers[user] = marker

	def toast_status(self):
		configuration = ConfigParser()
		configuration.read('data/settings/config.ini')
		return configuration.getboolean('xmpp', 'toast_all')

	def xmpp_log(self, log_type, log):
		if log_type == 'info':
			self.xmpp_client.logger.info(log)

	def error_dialogue(self, msg):
		"""
		Popup confirming with the user whether they want to exit the application.
		"""
		self.logger.error(str(msg[0]) + ": " + str(msg[1]))
		confirmation_box = BoxLayout(orientation='vertical')
		confirmation_box.add_widget(Label(text=str(msg[1])))
		box_int = BoxLayout(orientation='horizontal', spacing=50)
		close_button = Button(text='Close')
		close_button.bind(on_release=lambda x: self.stop())
		box_int.add_widget(close_button)
		confirmation_box.add_widget(box_int)
		self.confirmation_popup = Popup(title='Error with Config', content=confirmation_box, size_hint=(.7, None), size=(500, 500), auto_dismiss=False)
		self.confirmation_popup.open()

	@run_on_ui_thread
	def android_setflag(self):
		PythonActivity.mActivity.getWindow().addFlags(Params.FLAG_KEEP_SCREEN_ON)

if __name__ == '__main__':
	logging.captureWarnings(True)
	MainApp().run()
