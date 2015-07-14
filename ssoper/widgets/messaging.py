# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

import time
import os
import functools
import logging

import xml.etree.ElementTree as ET

from jnius import autoclass

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.graphics import Color, Rectangle, Line
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.app import App

from third_party.kivy_toaster.src.toast.androidtoast import toast

class MessageWidget(ScrollView):
	def __init__(self, *args, **kwargs):
		super(MessageWidget, self).__init__(*args, **kwargs)
		self.message_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
		self.message_layout.bind(minimum_height=self.message_layout.setter('height'))
		self.sub_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
		self.sub_layout.bind(minimum_height=self.sub_layout.setter('height'))
		bkgrnd_color = (0, 0, 0, 1)
		self.set_background(self.message_layout, bkgrnd_color)
		self.users = {}
		self.logger = logging.getLogger("kivy.operator.widgets.messaging")
		self.messages = {}
		Window.softinput_mode='pan'
		self.chatting = None
		self.reply = TextInput()
		self.main_app = App.get_running_app()
		self.gen_menu()

	def set_background(self, layout, color):
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
		
	def get_users(self):
		users = self.main_app.get_users()
		self.users = {}
		for user in users:
			self.users[user.split('@')[0]] = user
		self.logger.info('updating user list')
		if not self.chatting:
			self.gen_menu()

	def gen_menu(self):
		"""
		Checks to see if a notes file has ever been written. If so, it loads what has been previously saved.
		If not, then it adjusts the text input accordingly.
		"""
		self.chatting = None
		self.clear_widgets()
		self.message_layout.clear_widgets()
		sub_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
		sub_layout.bind(minimum_height=sub_layout.setter('height'))
		sub_layout.clear_widgets()
		names = []
		for user in self.users:
			names.append(user)
		names.sort()
		for name in names:
			lab = Button(text=name, size_hint_y=None, height=100, on_release=functools.partial(self.chat_panel, name))
			sub_layout.add_widget(lab)
		refresh = Button(text="Refresh Users", size_hint_y=None, on_release=lambda x: self.get_users(), height=100)
		self.message_layout.add_widget(refresh)
		self.message_layout.add_widget(sub_layout)
		self.add_widget(self.message_layout)

	def on_message_receive(self, msg):
		sender = str(msg['from']).strip()
		text = str(msg['body']).strip()
		chk_sender = sender.split('@')[0]

		if self.chatting == chk_sender:
			self.sub_layout.add_widget(Label(text=chk_sender + ": " + text, size_hint_y=None, height=80, halign='left'))
		if sender in self.messages:
			self.logger.info('receving new message from ' + sender)
			self.messages[sender].append(text)
		else:
			self.logger.info('receving first message from ' + sender)
			self.messages[sender] = [text]

		print(self.messages)

	def chat_panel(self, user, event):
		self.names = {}
		for name in self.messages:
			self.names[name.split('@')[0]] = name
		self.chatting = user
		self.clear_widgets()
		self.message_layout.clear_widgets()
		self.sub_layout.clear_widgets()
		if user in self.names:
			self.new = False
			temp = self.messages[self.names[user]]
			for msg in temp:
				lab = Label(text=user + ": " + msg, size_hint_y=None, height=80, halign='left')
				self.sub_layout.add_widget(lab)
		else:
			self.new_lab = Label(text="Start a new conversation with " + user + "!")
			"""with self.new_lab.canvas.after:
				Color(1, 0, 0)
				Line(rectangle =(self.new_lab.x+1,self.new_lab.y+1,self.new_lab.width-1,self.new_lab.height-1))
				Color(1, 1, 1)"""
			self.new = True
			self.sub_layout.add_widget(self.new_lab)
		bottom = BoxLayout(size_hint_y=None, height=80)
		self.reply = TextInput(hint_text="Write a message...")
		send = Button(text="Send", size_hint_x=.2, on_release=functools.partial(self.send_message, user))
		bottom.add_widget(self.reply)
		bottom.add_widget(send)
		header = BoxLayout(size_hint_y=None, height=80)
		back_btn = Button(text='< Recent', size_hint_x=.3, on_release=lambda x: self.gen_menu())
		title = Label(text=user, halign='left')
		presence = Label(size_hint_x=.3)
		header.add_widget(back_btn)
		header.add_widget(title)
		header.add_widget(presence)
		self.message_layout.add_widget(header)
		self.message_layout.add_widget(self.sub_layout)
		self.message_layout.add_widget(bottom)
		self.add_widget(self.message_layout)

	def send_message(self, user, event):
		recipient = self.users[user]
		msg = self.reply.text
		if msg:
			self.main_app.send_message(msg, user)
			self.sub_layout.add_widget(Label(text=msg, size_hint_y=None, height=80, halign='right'))
			self.reply.text = ""
			if self.new:
				self.sub_layout.remove_widget(self.new_lab)
