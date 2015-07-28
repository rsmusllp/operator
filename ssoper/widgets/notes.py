# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

import os

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from third_party.kivy_toaster.src.toast.androidtoast import toast

class NotesWidget(BoxLayout):
	def __init__(self, *args, **kwargs):
		super(NotesWidget, self).__init__(*args, **kwargs)
		self.note_layout = BoxLayout(orientation='vertical')
		self.open_data()

	def open_data(self):
		"""
		Checks to see if a notes file has ever been written. If so, it loads what has been previously saved.
		If not, then it adjusts the text input accordingly.
		"""
		if os.path.isfile('/sdcard/operator/notes.txt'):
			f = open('/sdcard/operator/notes.txt', 'r')
			data = ""
			for line in f:
				data = data + line
			self.text_input = TextInput(text=data, multiline=True, size_hint=(1, .9))
		else:
			f = open('/sdcard/operator/notes.txt', 'w')
			self.text_input = TextInput(hint_text="Put your notes here", multiline=True, size_hint=(1, .9))

		self.note_layout.add_widget(self.text_input)
		self.save_button = Button(text="Save", on_release=lambda x: self.save_data(), size_hint=(1, .1))
		self.note_layout.add_widget(self.save_button)
		self.add_widget(self.note_layout)
		f.close()

	def save_data(self):
		"""
		When the user presses save, it saves what has been written to a file on the disk.
		"""
		f = open('/sdcard/operator/notes.txt', 'w')
		f.write(self.text_input.text)
		toast("Notes saved to disk", True)
		f.close()
