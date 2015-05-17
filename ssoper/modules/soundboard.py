# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

from kivy.core.audio import SoundLoader

def play_sound(sound_file):
	"""
	Play a WAV sound file.

	:param str sound_file: The path to the WAV file to play.
	"""
	sl = SoundLoader()
	sound = sl.load(sound_file)
	sound.play()
