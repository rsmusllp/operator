#!/usr/bin/env python

from kivy.core.audio import SoundLoader

class SoundBoard(SoundLoader):

	def do_play_sound(self, sound_file):
		# load a sound and play it
		sound = self.load(sound_file)
		sound.play()

def do_play_sound(sound_file):
	sl = SoundLoader()
	sl.load(sound_file)
	sl.play()