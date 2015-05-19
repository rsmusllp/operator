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

from kivy.uix.boxlayout import BoxLayout

class RootWidget(BoxLayout):
	def __init__(self, *args, **kwargs):
		super(RootWidget, self).__init__(*args, **kwargs)
		self.logger = logging.getLogger("kivy.operator.widgets.root")
		self._sound_recorder = None

	def do_play_sound(self, sound_file):
		soundboard.play_sound(sound_file)

	def do_start_recording(self):
		if self._sound_recorder:
			return
		self._sound_recorder = recorder.SoundRecorder()
		self._sound_recorder.start()

	def do_stop_recording(self):
		if not self._sound_recorder:
			return
		self._sound_recorder.stop()
		self._sound_recorder = None

	def do_take_picture(self):
		camera.take_picture()

