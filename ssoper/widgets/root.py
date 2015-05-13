# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

import logging

from ssoper.modules import camera
from ssoper.modules import soundboard

from kivy.uix.boxlayout import BoxLayout

class RootWidget(BoxLayout):
	def __init__(self, *args, **kwargs):
		self.logger = logging.getLogger("kivy.operator.{0}".format(self.__class__.__name__))
		super(RootWidget, self).__init__(*args, **kwargs)

	def do_play_sound(self, sound_file):
		soundboard.play_sound(sound_file)

	def do_take_picture(self):
		camera.take_picture()
