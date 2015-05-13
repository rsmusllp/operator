# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

from kivy.core.audio import SoundLoader

def play_sound(sound_file):
	sl = SoundLoader()
	sound = sl.load(sound_file)
	sound.play()
