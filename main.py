#!/usr/bin/env python

import logging
from os import chdir, getcwd, mkdir
from os.path import exists
from time import strftime

from kivy import platform
from kivy.app import App
from kivy.core.audio import SoundLoader
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput

android = False
LOGFILE = getcwd() + "/OPERATOR_LOG.txt"
logging.basicConfig(filename=LOGFILE,level=logging.DEBUG,)

if platform =='android':
	from plyer import camera
 	android = True


class FileManager():
# class to manager file operations

	def create_directory(dir_name):
		# create a directory
		directory = self.normalize_directory(self.dir_name)
		dirs = directory.split('/')
		cwd = getcwd()
		counter = 1
		for my_dir in dirs:
			if counter == 1:
				my_dir = '/' + my_dir
				counter += 1
			if exists(my_dir):
				chdir(my_dir)
			else:
				try:
					mkdir(my_dir)
				except:
					pass
				chdir(my_dir)
		chdir(cwd)
		return

	def normalize_directory(dir_name):
		# remove begining and trailing / from directory
		directory = self.dir_name
		n_directory = directory.strip('/')
		return n_directory

	def verify_file_exists(file_name):
		# check if a file exists
		file_exists = False
		full_file_name = self.dir_name + self.file_name
		if exists(full_file_name):
			file_exists = True
		return file_exists



class Operator(AnchorLayout):
	
	fm = FileManager()

	def do_play_sound(self, sound_file):
		# load a sound and play it
		sound = SoundLoader.load(sound_file)
		sound.play()
		return

	def do_take_picture(self):
		# take a picture and save it
		logging.debug('do_take_picture')
		
		if android == False:
			print('Camera is not implemented on this platform')
			logging.debug('\nandroid = false')
		else:
			logging.debug('\nandroid = true')
			output_directory = getcwd() + '/'
			logging.debug('\ngot cwd')
			picture_name = str(strftime('%Y-%m-%d-%H-%M-%S')) + '.jpg'
			logging.debug('\ncreated picture name')
			picture_output = output_directory + picture_name
			logging.debug('\ncreated full picture name')
			try:
				logging.debug('\nattempting to take picture')
				camera.take_picture(picture_output, self.verify_image_saved(picture_output))
				logging.debug('\ntook picture')
			except:
				logging.exception('Got exception on main handler')
				raise

	def verify_image_saved(self, file_name):
		# check that the image was saved correctly
		success = exists(file_name)
		return True

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