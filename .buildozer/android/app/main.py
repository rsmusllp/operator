#!/usr/bin/env python

import datetime
import wave

from audiostream import get_input
from kivy.app import App
from kivy.core.audio import SoundLoader
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput

class Operator(AnchorLayout):
	
	def do_play_sound(self, sound_file):
		# load a sound and play it
		sound = SoundLoader.load(sound_file)
		sound.play()
		return

	# def do_start_record_sound():
	# 	mic = get_input(callback=mic_callback)
	# 	mic.start()


	# def mic_callback(buf):
	# 	mic_frames.append(buf)	


class MainApp(App):
    def build(self):
        return Operator()

    def on_pause(self):
    
    	return True

    def on_resume(self):
    	pass
    	return

if __name__ == '__main__':
    MainApp().run()