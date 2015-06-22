# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

import logging
import threading

from ssoper.modules import camera
from ssoper.modules import recorder
from ssoper.modules import soundboard
from ssoper.utilities import popups

from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.app import App

class RootWidget(BoxLayout):
	screen_manager = ObjectProperty(None)
	def __init__(self, *args, **kwargs):
		super(RootWidget, self).__init__(*args, **kwargs)
		self.logger = logging.getLogger("kivy.operator.widgets.root")
		self._sound_recorder = None
		self.list_of_prev_screens = []
		self.confirmation_popup = Popup()

	def do_play_sound(self, sound_file):
		soundboard.play_sound(sound_file)

	def do_start_recording(self):
		if self._sound_recorder:
			popups.popup_warn('Warning', 'Recorder was previously started')
			return
		self._sound_recorder = recorder.SoundRecorder()
		self._sound_recorder.start()
		popups.popup_good('Success', 'Recorder was started')

	def do_stop_recording(self):
		if not self._sound_recorder:
			popups.popup_warn('Warning', 'Recorder has not been started')
			return
		self._sound_recorder.stop()
		self._sound_recorder = None
		popups.popup_good('Success', 'Recorder was stopped')

	def do_take_picture(self):
		camera.take_picture()

	def onBackBtn(self):
		if self.list_of_prev_screens:
			self.screen_manager.current = self.list_of_prev_screens.pop()
			return True
		else:
			self.prompt_close()
			return True

	def do_set_screen(self, btn, next_screen):
		current_screen_name = self.screen_manager.current_screen.name
		if not current_screen_name == next_screen:
			self.list_of_prev_screens.append(current_screen_name)
		self.screen_manager.current = next_screen

	def prompt_close(self):
		confirmation_box = BoxLayout(orientation='vertical')
		confirmation_box.add_widget(Label(text='Do you want to close Operator?'))
		box_int = BoxLayout(orientation='horizontal')
		affirm_button = Button(text='Yes')
		affirm_button.bind(on_release=lambda x: self.choice_false())
		dismiss_button = Button(text='Cancel')
		dismiss_button.bind(on_release=lambda x: self.choice_cancel())
		box_int.add_widget(affirm_button)
		box_int.add_widget(dismiss_button)
		confirmation_box.add_widget(box_int)
		self.confirmation_popup = Popup(title='Confirmation', content=confirmation_box, size_hint=(None, None), size=(500, 500), auto_dismiss=False)
		self.confirmation_popup.open()

	def choice_cancel(self):
		self.confirmation_popup.dismiss()

	def choice_false(self):
		self.confirmation_popup.dismiss()
		App.get_running_app().stop()

