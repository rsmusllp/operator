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

from ssoper.modules.xmpp import OperatorXMPPClient
from ssoper.widgets.root import RootWidget

from kivy.app import App
from kivy.factory import Factory
from kivy.core.window import Window

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

PythonActivity = autoclass('org.renpy.android.PythonActivity')
View = autoclass('android.view.View')
Params = autoclass('android.view.WindowManager$LayoutParams')

class MainApp(App):
	def __init__(self, *args, **kwargs):
		super(MainApp, self).__init__(*args, **kwargs)
		self.logger = logging.getLogger('kivy.operator.app')
		self.map = None
		self.xmpp_client = None
		self.user_location_markers = {}
		self._last_location_update = 0
		Window.bind(on_keyboard=self.on_back_btn)
		self.android_setflag()

	def build(self):
		self.root = RootWidget()
		self.xmpp_client = OperatorXMPPClient(
			sz_utils.parse_server(self.config.get('xmpp', 'server'), 5222),
			self.config.get('xmpp', 'username'),
			self.config.get('xmpp', 'password'),
			self.config.get('xmpp', 'room')
		)
		self.map = self.root.ids.map_panel_widget.ids.map_widget
		self.messaging = self.root.ids.message_menu
		self.xmpp_client.bind(on_user_location_update=self.on_user_location_update)
		self.xmpp_client.bind(on_message_receive=self.on_message_receive)
		self.xmpp_client.bind(on_muc_receive=self.on_muc_receive)
		gps.configure(on_location=self.on_gps_location)
		gps.start()

		if not os.path.isdir("/sdcard/operator"):
			os.makedirs("/sdcard/operator")

		return self.root

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
		custom_config = os.path.join(os.path.dirname(__file__), 'config.ini')
		if os.path.isfile(custom_config):
			self.logger.info('loading custom config: {0}'.format(custom_config))
			config.update_config(custom_config, overwrite=False)

	def build_settings(self, settings):
		settings.add_json_panel('Operator Settings', self.config, 'data/settings_panel.json')

	def on_message_receive(self, event, msg):
		self.messaging.on_message_receive(msg)

	def on_muc_receive(self, event, msg):
		self.messaging.on_muc_receive(msg)

	def on_gps_location(self, **kwargs):
		# kwargs on Galaxy S5 contain:
		#   altitude, bearing, lat, lon, speed
		if not ('lat' in kwargs and 'lon' in kwargs):
			return
		current_time = time.time()
		if current_time - self._last_location_update < sz_utils.parse_timespan(self.config.get('miscellaneous', 'gps_update_freq')):
			return
		latitude = kwargs.pop('lat')
		longitude = kwargs.pop('lon')
		altitude = kwargs.pop('altitude', None)
		bearing = kwargs.pop('bearing', None)
		speed = kwargs.pop('speed', None)

		self.map.update_location((latitude, longitude), altitude, bearing, speed)
		self.xmpp_client.update_location((latitude, longitude), altitude, bearing, speed)
		self.messaging.get_users()
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
			icon_color=icon_color
		)
		self.user_location_markers[user] = marker

	def xmpp_log(self, log_type, log):
		if log_type == 'info':
			self.xmpp_client.logger.info(log)

	@run_on_ui_thread
	def android_setflag(self):
		PythonActivity.mActivity.getWindow().addFlags(Params.FLAG_KEEP_SCREEN_ON)

if __name__ == '__main__':
	logging.captureWarnings(True)
	MainApp().run()
