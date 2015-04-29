#!/usr/bin/env python

from kivy.app import App
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput

class Operator(AnchorLayout):
    pass

class MainApp(App):
    def build(self):
        return Operator()

    def on_pause(self):
    
    	return True

    def on_resume(self):

    	return True    

if __name__ == '__main__':
    MainApp().run()