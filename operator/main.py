#!/usr/bin/env python

__version__ = '0.1'

from kivy import platform
from kivy.app import App
from kivy.core.audio import SoundLoader
from kivy.uix.boxlayout import BoxLayout

on_android = False

if platform == 'android':
	from modules.camera import Camera
	on_android = True


class Operator(BoxLayout):
	def __init__(self, *args, **kwargs):
		self.logger = logging.getLogger("kivy.operator.{0}".format(self.__class__.__name__))
		super(Operator, self).__init__(*args, **kwargs)

class MainApp(App):
	def build(self):
		return Operator()

	def on_pause(self):
		return True

	def on_resume(self):
		pass

if __name__ == '__main__':
	MainApp().run()
