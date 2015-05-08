#!/usr/bin/env python

__version__ = "0.1"

from os import chdir, getcwd, mkdir
from os.path import exists
from time import strftime

from kivy import platform
from kivy.app import App
from kivy.core.audio import SoundLoader
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

android = False

if platform =='android':
	from plyer import camera
 	android = True



class Operator(BoxLayout):

	def do_play_sound(self, sound_file):
		# load a sound and play it
		sound = SoundLoader.load(sound_file)
		sound.play()
		return

	def do_take_picture(self):
		# take a picture and save it
		if android == False:
			print('Camera is not implemented on this platform')
		else:
			picture_name = str(strftime('%Y-%m-%d-%H-%M-%S')) + '.jpg'
			picture_output = '/storage/sdcard0/' + picture_name
			try:
				camera.take_picture(picture_output, self.verify_image_saved(picture_output))
			except:
				raise

	def verify_image_saved(self, file_name):
		# check that the image was saved correctly
		success = exists(file_name)
		return success



class MainApp(App):
    def build(self):
        operator = Operator()
        return operator

    def on_pause(self):
    	return True

    def on_resume(self):
    	pass

if __name__ == '__main__':
    MainApp().run()