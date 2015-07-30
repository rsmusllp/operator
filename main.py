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
#import ConfigParser

from ssoper.modules.xmpp import OperatorXMPPClient
from ssoper.widgets.root import RootWidget

from kivy.app import App
from kivy.factory import Factory
from kivy.core.window import Window
from kivy.config import ConfigParser
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
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

CONFIG_PATH = 'data/settings/config.ini'
DEFAULT_CONFIG_PATH = 'data/settings/config.example.ini'
MANDATORY_XMPP_OPTIONS = ('username', 'password', 'server')

PythonActivity = autoclass('org.renpy.android.PythonActivity')
Params = autoclass('android.view.WindowManager$LayoutParams')
View = autoclass('android.view.View')

class MainApp(App):
	def __init__(self, *args, **kwargs):
		super(MainApp, self).__init__(*args, **kwargs)
		self.logger = logging.getLogger('kivy.operator.app')
		if not os.path.isdir("/sdcard/operator"):
			os.makedirs("/sdcard/operator")
		self.map = None
		self.messaging = None
		self.xmpp_client = None
		self.user_location_markers = {}
		self._last_location_update = 0
		Window.bind(on_keyboard=self.on_back_btn)
		self.android_setflag()
		self.xmpp_config_ok = False
		self.start = True
		self.confirmation_popup = Popup()
		self.lock_btn_presses = []
		self.configuration = ConfigParser()
		self.configuration.read(CONFIG_PATH)
		self.check_config()

	def check_config(self):
		"""
		Checks to see if the config has the required XMPP fields filled out accordingly.
		Then, it evaluates the config file to make sure that all fields exist, at least corresponding to the
		example config file.
		"""
		conf = self.configuration

		if conf.has_section('xmpp'):
			if all(conf.has_option('xmpp', k) and conf.get('xmpp', k) for k in MANDATORY_XMPP_OPTIONS):
				self.xmpp_config_ok = True

		def_conf = ConfigParser()
		def_conf.read(DEFAULT_CONFIG_PATH)

		for section in def_conf.sections():
			if conf.has_section(section):
				for option in def_conf.options(section):
					if not conf.has_option(section, option) or conf.get(section, option) is None:
						conf.set(section, option, def_conf.get(section, option))
			else:
				conf.add_section(section)
				for option in def_conf.options(section):
					conf.set(section, option, def_conf.get(section, option))

		self.configuration = conf
		self.configuration.write()

	def build(self):
		self.root = RootWidget()
		if self.xmpp_config_ok:
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
		else:
			self.logger.warning("XMMP config invalid, disabling XMPP operations")

		self.map = self.root.ids.map_panel_widget.ids.map_widget
		self.messaging = self.root.ids.message_menu
		gps.configure(on_location=self.on_gps_location)
		gps.start()
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
		custom_config = 'data/settings/config.ini'
		if os.path.isfile(custom_config):
			self.logger.info('loading custom config: {0}'.format(custom_config))
			config.update_config(custom_config, overwrite=False)

	def build_settings(self, settings):
		settings.add_json_panel('XMPP', self.configuration, 'data/settings/xmpp.json')
		settings.add_json_panel('Map', self.configuration, 'data/settings/map.json')

	def on_message_receive(self, event, msg):
		self.messaging.on_message_receive(msg)

	def on_muc_receive(self, event, msg):
		self.messaging.on_muc_receive(msg)

	def on_gps_location(self, **kwargs):
		# kwargs on Galaxy S5 contain:
		#   altitude, bearing, lat, lon, speed
		if self.start:
			if self.xmpp_client:
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
		if self.xmpp_client:
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
		self.map.save_marker_file()
		if self.xmpp_client:
			self.xmpp_client.shutdown()

	def on_user_location_update(self, _, info):
		if not self.map.is_ready:
			self.logger.warning('map is not ready for user marker')
			return
		user = info['user']
		if user in self.user_location_markers:
			self.user_location_markers[user].remove()
		if self.xmpp_client:
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
		return self.configuration.getboolean('xmpp', 'toast_all')

	def xmpp_log(self, log_type, log):
		if log_type == 'info':
			self.xmpp_client.logger.info(log)

	def prompt_lock_screen(self):
		"""
		Popup confirming with the user whether they want to lock the screen.
		"""
		confirmation_box = BoxLayout(orientation='vertical')
		confirmation_box.add_widget(Label(text='Do you want to lock the screen?'))
		box_int = BoxLayout(orientation='horizontal', spacing=50)
		affirm_button = Button(text='Yes')
		affirm_button.bind(on_release=lambda x: self.lock_screen())
		dismiss_button = Button(text='Cancel')
		dismiss_button.bind(on_release=lambda x: self.confirmation_popup.dismiss())
		box_int.add_widget(affirm_button)
		box_int.add_widget(dismiss_button)
		confirmation_box.add_widget(box_int)
		self.confirmation_popup = Popup(title='Confirmation', content=confirmation_box, size_hint=(.7, None), size=(500, 500), auto_dismiss=False)
		self.confirmation_popup.open()

	@run_on_ui_thread
	def lock_screen(self):
		"""
		Lock the screen by going to a black layout and not allowing input. Will disable after 10 taps.
		"""
		self.confirmation_popup.dismiss()
		flag = View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
		PythonActivity.mActivity.getWindow().getDecorView().setSystemUiVisibility(flag)
		mb = True
		for child in self.root.walk():
			if hasattr(child, 'name'):
				if child.name == 'root' and mb:
					self.removed = child
					child.parent.remove_widget(child)
					mb = False
		self.bl = BoxLayout(orientation='vertical')
		self.bl.add_widget(
			Button(
				size_hint=(1, 1),
				background_color=[0, 0, 0, 1],
				on_release=lambda x: self.lock_button()
			)
		)
		self.root.add_widget(self.bl)

	def lock_button(self):
		"""
		Registers clicks on the locked screen. Only counts clicks within 10 second gap.
		"""
		current_time = time.time()
		self.lock_btn_presses.append(current_time)
		while current_time - self.lock_btn_presses[0] > self.configuration.getint('miscellaneous', 'lockout_timeout'):
			del self.lock_btn_presses[0]

		if len(self.lock_btn_presses) == self.configuration.getint('miscellaneous', 'lockout_clicks'):
			self.root.remove_widget(self.bl)
			self.root.add_widget(self.removed)
			self.lock_btn_presses = []

	@run_on_ui_thread
	def android_setflag(self):
		PythonActivity.mActivity.getWindow().addFlags(Params.FLAG_KEEP_SCREEN_ON)

	def update_mood(self, mood):
		if self.xmpp_client:
			self.xmpp_client.update_mood(mood)

if __name__ == '__main__':
	logging.captureWarnings(True)
	MainApp().run()
