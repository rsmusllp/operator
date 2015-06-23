# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

import os
import functools
import shutil

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.core.audio import SoundLoader
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, Rectangle
from kivy.uix.popup import Popup

from ssoper.widgets.fileselect import FileWidget

from third_party.kivy_toaster.src.toast.androidtoast import toast

class SoundboardWidget(ScrollView):
	def __init__(self, *args, **kwargs):
		super(SoundboardWidget, self).__init__(*args, **kwargs)
		self.sound_menu_layout = GridLayout(cols=1)
		self.play_layout = GridLayout(cols=1)
		self.filewidget = FileWidget()
		self.file_select_popup = Popup()
		self.set_background(self.sound_menu_layout)
		self.load_sounds()

	def set_background(self, layout):
		"""
		Sets a solid color as a background.

		:param layout: The layout for whichever part of the screen should be set.
		"""
		layout.bind(size=self._update_rect, pos=self._update_rect)

		with layout.canvas.before:
			Color(0, 0, 0, 1)
			self.rect = Rectangle(size=layout.size, pos=layout.pos)

	def _update_rect(self, instance, value):
		"""
		Ensures that the canvas fits to the screen should the layout ever change.
		"""
		self.rect.pos = instance.pos
		self.rect.size = instance.size

	def load_sounds(self):
		"""
		Creates a list of all sounds located in the appropriate directory, as well as button to add more.
		"""
		if not os.path.isdir("/sdcard/operator/sounds"):
			os.makedirs("/sdcard/operator/sounds")
		self.clear_widgets()
		self.sound_menu_layout.clear_widgets()
		titles = []
		paths = []
		new_wav_button = Button(text="Load new WAV", size_hint_y=None)
		new_wav_button.bind(on_release=lambda x: self.do_popup_file_select())
		self.sound_menu_layout.add_widget(new_wav_button)
		for filename in os.listdir("/sdcard/operator/sounds"):
			if filename.endswith(".wav"):
				paths.append(os.path.join("/sdcard/operator/sounds/", filename))
				name = filename[:-4].title()
				titles.append(name)
		for title, path in zip(titles, paths):
			sound_button = Button(text=title, size_hint_y=None)
			sound_button.bind(on_release=functools.partial(self.play_button, path))
			self.sound_menu_layout.add_widget(sound_button)
		self.add_widget(self.sound_menu_layout)

	def play_button(self, sound_file, event):
		"""
		Screen that shows play button as full screen option, making it easier to press.

		:param str sound_file: The path to the WAV file to play.
		"""
		self.play_layout.clear_widgets()
		play_button = Button(text="PLAY", size_hint=(1, .9))
		play_button.bind(on_release=functools.partial(self.play_sound, sound_file))
		return_button = Button(text="Previous", size_hint=(1, .1))
		return_button.bind(on_release=lambda x: self.show_menu())
		self.play_layout.add_widget(play_button)
		self.play_layout.add_widget(return_button)
		self.clear_widgets()
		self.add_widget(self.play_layout)

	def play_sound(self, sound_file, event):
		"""
		Play a WAV sound file.

		:param str sound_file: The path to the WAV file to play.
		"""
		sl = SoundLoader()
		sound = sl.load(sound_file)
		sound.play()

	def show_menu(self):
		"""
		Shows the list of possible sounds.
		"""
		self.clear_widgets()
		self.add_widget(self.sound_menu_layout)

	def do_popup_file_select(self):
		"""
		Prompts the user to navigate to the WAV file.
		"""
		self.filewidget = FileWidget()
		box = BoxLayout(orientation='vertical')
		box_int = BoxLayout(orientation='horizontal', size_hint=(1, .2))
		close_button = Button(text='Load')
		close_button.bind(on_release=lambda x: self.copy_sound())
		dismiss_button = Button(text='Cancel')
		dismiss_button.bind(on_release=lambda x: self.file_select_popup.dismiss())
		box.clear_widgets()
		box_int.add_widget(close_button)
		box_int.add_widget(dismiss_button)
		box.add_widget(self.filewidget)
		box.add_widget(box_int)
		self.file_select_popup = Popup(title='Choose File', content=box, size_hint=(None, None), size=(800, 1000), auto_dismiss=False)
		self.file_select_popup.open()

	def do_load_true_path(self, path, filename):
		"""
		Does a series of a checks to make sure the file that is trying to be loaded is valid.

		:param str path: The directory of the file.
		:param list filename: The name of the file.
		:return: The path to the validated WAV file. If the path is deemed invalid, None is returned.
		:rtype: str
		"""
		if path is None or not os.path.isfile(filename[0]):
			toast("Not a valid path!", True)
			return
		full_path = os.path.join(path, filename[0])
		if not os.access(full_path, (os.R_OK | os.W_OK)):
			toast("No permission, please move file", True)
			return
		if not str(filename[0]).endswith('.wav'):
			toast("Not a WAV file!", True)
			return
		with open(full_path) as f:
			path_list = str(f).split("'")
			true_path = path_list[1]
		if not os.path.exists(true_path):
			toast("Not a valid path!", True)
		return true_path

	def copy_sound(self):
		"""
		Copies the WAV file to the proper directory.
		"""
		path = self.do_load_true_path(self.filewidget.path, self.filewidget.filename)
		if path is not None:
			sep = path.split("/")
			name = sep[len(sep) - 1]
			d = "/sdcard/operator/sounds/"
			open(os.path.join(d, name), 'a')
			shutil.copyfile(str(path), d + name)
			self.load_sounds()
			self.file_select_popup.dismiss()
