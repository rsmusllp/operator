# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

import logging

from ssoper.modules import camera
from ssoper.modules import recorder
from ssoper.modules import soundboard
from ssoper.utilities import popups

from kivy.properties import ObjectProperty

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen

class RootWidget(BoxLayout):
	screen_manager = ObjectProperty(None)
	def __init__(self, *args, **kwargs):
		super(RootWidget, self).__init__(*args, **kwargs)
		self.logger = logging.getLogger("kivy.operator.widgets.root")
		self._sound_recorder = None
		self._prev_screens = []
		self.list_of_prev_screens = []

	def do_play_sound(self, sound_file):
		soundboard.play_sound(sound_file)

	"""
	def do_set_screen(self, btn, next_screen):
		if hasattr(btn.parent, 'name'):
			self._prev_screens.append(btn.parent.name)
		self.screen_manager.current = next_screen
	"""

	def do_start_recording(self):
		if self._sound_recorder:
			popups.popup_warn('Warning', 'Recorder was previously started')
			return
		self._sound_recorder = recorder.SoundRecorder()
		self._sound_recorder.start()
		popups.popup_good('Success', 'Recorder was started')

	def do_stop_recording(self):
		if not self._sound_recorder:
			popups.popup_warn('Warning', 'Recorder has not been started')
			return
		self._sound_recorder.stop()
		self._sound_recorder = None
		popups.popup_good('Success', 'Recorder was stopped')

	def do_take_picture(self):
		camera.take_picture()

	def onBackBtn(self):
		if self.list_of_prev_screens:
			self.screen_manager.current = self.list_of_prev_screens.pop()
			return True
		else:
			self.screen_manager.current = "Home"
			return True

	def do_set_screen(self, btn, next_screen):
		loc = btn.parent
		try:
			if loc.name == "bar":
				self.title = "Home"
		except AttributeError:
			while not isinstance(loc, Screen):
				loc = loc.parent
			self.title = loc.name

		self.list_of_prev_screens.append(self.title)
		self.screen_manager.current = next_screen
