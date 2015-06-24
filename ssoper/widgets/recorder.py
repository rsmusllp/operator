# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

import time
import os
import functools

from jnius import autoclass

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, Rectangle
from kivy.core.audio import SoundLoader

from third_party.kivy_toaster.src.toast.androidtoast import toast

MediaRecorder = autoclass('android.media.MediaRecorder')
AudioSource = autoclass('android.media.MediaRecorder$AudioSource')
OutputFormat = autoclass('android.media.MediaRecorder$OutputFormat')
AudioEncoder = autoclass('android.media.MediaRecorder$AudioEncoder')
File = autoclass('java.io.File')

class RecorderWidget(ScrollView):
	def __init__(self, *args, **kwargs):
		super(RecorderWidget, self).__init__(*args, **kwargs)
		self.first_layout = BoxLayout(orientation='vertical')
		self.record_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
		self.record_layout.bind(minimum_height=self.record_layout.setter('height'))
		self.list_layout = ScrollView()
		self.recorder = MediaRecorder()
		if not os.path.isdir("/sdcard/operator/recordings"):
			os.makedirs("/sdcard/operator/recordings")
		self.is_recording = False
		self.set_background(self.record_layout)
		self.set_background(self.first_layout)
		self.layout_gen()

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

	def layout_gen(self):
		"""
		Generate the initial layout with the dynamic recording button.
		"""
		if not self.is_recording:
			rcrd_btn = Button(text="Start Recording", size_hint_y=.8)
			rcrd_btn.bind(on_release=lambda x: self.start())
		else:
			rcrd_btn = Button(text="Stop Recording", size_hint_y=.2)
			rcrd_btn.bind(on_release=lambda x: self.stop())
		list_btn = Button(text="Previous recordings", on_release=lambda x: self.prev_recordings(), size_hint_y=None, height=160)
		self.first_layout.clear_widgets()
		self.first_layout.add_widget(rcrd_btn)
		self.first_layout.add_widget(list_btn)
		self.clear_widgets()
		self.add_widget(self.first_layout)

	def init_recorder(self):
		"""Initialize the recorder."""
		storage_path = '/sdcard/operator/recordings/' + time.strftime('%Y-%m-%d-%H-%M-%S') + '.wav'
		self.recorder.setAudioSource(AudioSource.MIC)
		self.recorder.setOutputFormat(OutputFormat.THREE_GPP)
		self.recorder.setAudioEncoder(AudioEncoder.AMR_NB)
		self.recorder.setOutputFile(storage_path)
		self.recorder.prepare()

	def start(self):
		"""Start the recorder."""
		if self.is_recording:
			self.recorder.stop()
			self.recorder.reset()
			self.is_recording = False
			return

		self.init_recorder()
		self.recorder.start()
		self.is_recording = True
		self.layout_gen()
		toast("Recording started", True)

	def stop(self):
		"""Stop the recorder."""
		if not self.is_recording:
			return
		self.recorder.stop()
		self.recorder.reset()
		self.is_recording = False
		self.layout_gen()
		toast("Recording saved", True)

	def prev_recordings(self):
		"""
		Show a list of previous recordings.
		"""
		self.clear_widgets()
		self.record_layout.clear_widgets()
		self.list_layout.clear_widgets()
		#sub_layout = BoxLayout(orientation='vertical')
		sub_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
		sub_layout.bind(minimum_height=sub_layout.setter('height'))
		sub_layout.clear_widgets()
		titles = []
		paths = []
		for filename in os.listdir("/sdcard/operator/recordings"):
			if filename.endswith(".wav"):
				paths.append(os.path.join("/sdcard/operator/recordings/", filename))
				name = filename[:-4]
				info = name.split('-')
				formatted_name = info[3] + ":" + info[4] + ":" + info[5] + " on " + info[1] + "/"+info[2] + "/" + info[0]
				titles.append(formatted_name)
		for title, path in zip(titles, paths):
			play_button = Button(text=title, size_hint_y=None, height=160)
			play_button.bind(on_release=functools.partial(self.play_prev, path))
			sub_layout.add_widget(play_button)
		return_btn = Button(text="Previous", on_release=lambda x: self.show_menu(), size_hint_y=None, height=100)
		#self.list_layout.add_widget(sub_layout)
		self.record_layout.add_widget(sub_layout)
		self.record_layout.add_widget(return_btn)
		self.add_widget(self.record_layout)

	def play_prev(self, path, event):
		"""
		Play the selected recording.

		:param str path: The path of the .wav recording.
		"""
		sl = SoundLoader()
		sound = sl.load(path)
		sound.play()

	def show_menu(self):
		"""
		Shows the list of possible sounds.
		"""
		self.clear_widgets()
		self.record_layout.clear_widgets()
		self.layout_gen()
