# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

from kivy.core.audio import SoundLoader

def do_play_sound(sound_file):
	sl = SoundLoader()
	sl.load(sound_file)
	sl.play()
