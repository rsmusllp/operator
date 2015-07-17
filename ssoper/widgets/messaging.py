# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

import functools
import logging

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.app import App

from third_party.kivy_toaster.src.toast.androidtoast import toast

class MessageWidget(BoxLayout):
	def __init__(self, *args, **kwargs):
		super(MessageWidget, self).__init__(*args, **kwargs)
		self.orientation = 'vertical'
		self.master_layout = ScrollView(size_hint=(1, 1))
		self.master_layout.bind(size=self.master_layout.setter('size'))
		self.message_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
		self.message_layout.bind(minimum_height=self.message_layout.setter('height'))
		self.sub_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
		self.sub_layout.bind(minimum_height=self.sub_layout.setter('height'))
		bkgrnd_color = (0, 0, 0, 1)
		self.set_background(self, bkgrnd_color)
		self.users = {}
		self.logger = logging.getLogger("kivy.operator.widgets.messaging")
		self.messages = {}
		Window.softinput_mode = 'pan'
		self.chatting = None
		self.reply = TextInput()
		self.main_app = App.get_running_app()
		self.gen_menu()
		self.new_lab = Label()
		self.new = False

	def set_background(self, layout, color):
		"""
		Sets a solid color as a background.

		:param layout: The layout for whichever part of the screen should be set.
		"""
		layout.bind(size=self._update_rect, pos=self._update_rect)

		with layout.canvas.before:
			Color(1, 1, 1, 1)
			self.rect = Rectangle(size=layout.size, pos=layout.pos)

	def _update_rect(self, instance, value):
		"""
		Ensures that the canvas fits to the screen should the layout ever change.
		"""
		self.rect.pos = instance.pos
		self.rect.size = instance.size

	def get_users(self):
		"""
		Pulls the list of users on the XMPP server.
		"""
		users = self.main_app.get_users()
		self.users = {}

		for user in users:
			self.users[user.split('@')[0]] = user

		self.users['Operator Group'] = 'operator@public.bt'
		self.logger.info('updating user list')

		if not self.chatting:
			self.gen_menu()

	def gen_menu(self):
		"""
		Creates the base menu which displays all users.
		"""
		self.chatting = None
		self.clear_widgets()
		self.master_layout.clear_widgets()
		self.message_layout.clear_widgets()
		sub_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
		sub_layout.bind(minimum_height=sub_layout.setter('height'))
		sub_layout.clear_widgets()
		names = []

		for user in self.users:
			names.append(user)

		names.sort()
		op_chat = Button(
			text='Group Chat: OPERATOR',
			size_hint_y=None,
			height=100,
			on_release=functools.partial(self.chat_panel, 'Operator Group')
		)
		sub_layout.add_widget(op_chat)

		for name in names:
			lab = Button(
				text=name,
				size_hint_y=None,
				height=100,
				on_release=functools.partial(self.chat_panel, name)
			)
			sub_layout.add_widget(lab)

		refresh = Button(
			text="Refresh Users",
			size_hint_y=None,
			on_release=lambda x: self.get_users(),
			height=100
		)
		self.message_layout.add_widget(refresh)
		self.message_layout.add_widget(sub_layout)
		self.master_layout.add_widget(self.message_layout)
		self.add_widget(self.master_layout)

	def on_message_receive(self, msg):
		"""
		Whenever a message is received, it is processed according to whatever the user is currently doing.

		:param Message msg: The XMPP message object.
		"""
		def redraw(self, args):
			"""
			Binds the size of the label background to the label size.
			"""
			self.bg_rect.size = self.size
			self.bg_rect.pos = self.pos

		sender = str(msg['from']).strip()
		text = str(msg['body']).strip()
		chk_sender = sender.split('@')[0]

		if self.chatting == chk_sender:
			lab = Label(
				text=chk_sender + ": " + text,
				size_hint_y=None,
				markup=True,
				halign='left'
			)

			lab.bind(width=lambda s, w:
				s.setter('text_size')(s, (w, None)))
			lab.bind(texture_size=lab.setter('size'))

			with lab.canvas:
				Color(self.name_to_txt(chk_sender), 1, 1, mode='hsv')

			with lab.canvas.before:
				Color(self.name_to_bg(chk_sender), 1, 1, mode='hsv')
				lab.bg_rect = Rectangle(pos=self.pos, size=self.size)

			lab.bind(pos=redraw, size=redraw)
			self.sub_layout.add_widget(lab)

			if self.new:
				self.sub_layout.remove_widget(self.new_lab)
				self.new = False

		if sender.split('/')[0] in self.messages:
			self.logger.info('receving new message from ' + sender)
			self.messages[sender.split('/')[0]].append([sender.split('@')[0], text])
		else:
			self.logger.info('receving first message from ' + sender)
			self.messages[sender.split('/')[0]] = [[sender.split('@')[0], text]]

	def on_muc_receive(self, msg):
		"""
		Whenever a group message is received, it is processed according to whatever the user is
		currently doing.

		:param Message msg: The XMPP message object.
		"""
		def redraw(self, args):
			"""
			Binds the size of the label background to the label size.
			"""
			self.bg_rect.size = self.size
			self.bg_rect.pos = self.pos

		sender = str(msg['from']).strip()
		text = str(msg['body']).strip()

		if self.chatting == "Operator Group":

			lab = Label(
				text=sender.split('/')[1] + ": " + text,
				size_hint_y=None,
				markup=True,
				halign='left'
			)

			lab.bind(width=lambda s, w:
				s.setter('text_size')(s, (w, None)))
			lab.bind(texture_size=lab.setter('size'))

			with lab.canvas.after:
				Color(self.name_to_txt(sender.split('/')[1]), 1, 1, mode='hsv')

			with lab.canvas.before:
				Color(self.name_to_bg(sender.split('/')[1]), 1, 1, mode='hsv')
				lab.bg_rect = Rectangle(pos=self.pos, size=self.size)

			lab.bind(pos=redraw, size=redraw)
			self.sub_layout.add_widget(lab)

			if self.new:
				self.sub_layout.remove_widget(self.new_lab)
				self.new = False

		else:
			toast(sender.split('/')[1] + ": " + text, True)

		if sender.split('/')[0] in self.messages:
			self.logger.info('receving new message from ' + sender)
			self.messages[sender.split('/')[0]].append([sender.split('/')[1], text])
		else:
			self.logger.info('receving first message from ' + sender)
			self.messages[sender.split('/')[0]] = [[sender.split('/')[1], text]]

	def chat_panel(self, user, event):
		"""
		Creates the actual chat screen where the messages are displayed and where the user can respond.

		:param str user: The username of whomever the user is chatting with.
		"""
		def redraw(self, args):
			"""
			Binds the size of the label background to the label size.
			"""
			self.bg_rect.size = self.size
			self.bg_rect.pos = self.pos

		full_name = self.users[user]
		self.chatting = user
		self.clear_widgets()
		self.master_layout.clear_widgets()
		self.message_layout.clear_widgets()
		self.sub_layout.clear_widgets()

		if full_name in self.messages:
			self.new = False
			temp = self.messages[full_name]
			for msg in temp:

				if not msg[0]:
					lab = Label(
						text=msg[1],
						color=(1, 1, 1, 1),
						size_hint_y=None,
						markup=True,
						halign='right'
					)

					lab.bind(width=lambda s, w:
						s.setter('text_size')(s, (w, None)))
					lab.bind(texture_size=lab.setter('size'))

					with lab.canvas.before:
						Color(.67, .82, 1, mode='hsv')
						lab.bg_rect = Rectangle(pos=self.pos, size=self.size)

					lab.bind(pos=redraw, size=redraw)
					self.sub_layout.add_widget(lab)
				else:
					lab = Label(
						text=msg[0] + ": " + msg[1],
						color=(0, 0, 0, 1),
						size_hint_y=None,
						markup=True,
						halign='left'
					)

					lab.bind(width=lambda s, w:
						s.setter('text_size')(s, (w, None)))
					lab.bind(texture_size=lab.setter('size'))

					with lab.canvas.before:
						Color(0, 0, .75, mode='hsv')
						lab.bg_rect = Rectangle(pos=self.pos, size=self.size)

					lab.bind(pos=redraw, size=redraw)
					self.sub_layout.add_widget(lab)

		else:
			self.new_lab = Label(text="Start a new conversation with " + user + "!", color=(0, 0, 0, 1)
			)
			self.new = True
			self.sub_layout.add_widget(self.new_lab)

		bottom = BoxLayout(size_hint_y=None, height=80)
		self.reply = TextInput(hint_text="Write a message...")
		title = Label(text=user, halign='left', color=(0, 0, 0, 1))

		send = Button(
			text="Send",
			size_hint_x=.2,
			on_release=functools.partial(self.send_message, full_name)
		)
		bottom.add_widget(self.reply)
		bottom.add_widget(send)
		header = BoxLayout(size_hint_y=None, height=80)
		back_btn = Button(text='< Recent', size_hint_x=.3, on_release=lambda x: self.gen_menu())
		presence = Label(size_hint_x=.3)
		header.add_widget(back_btn)
		header.add_widget(title)
		header.add_widget(presence)
		self.message_layout.add_widget(self.sub_layout)
		self.master_layout.add_widget(self.message_layout)
		self.add_widget(header)
		self.add_widget(self.master_layout)
		self.add_widget(bottom)

	def send_message(self, user, event):
		"""
		When the user hits the reply button, it sends the message back to the user (or group if it is
		a groupchat).

		:param str user: The username of whomever the user is chatting with.
		"""
		def redraw(self, args):
			"""
			Binds the size of the label background to the label size.
			"""
			self.bg_rect.size = self.size
			self.bg_rect.pos = self.pos

		msg = self.reply.text

		if msg:

			if user == self.users['Operator Group']:
				self.main_app.send_muc(msg, user)
			else:
				self.main_app.send_message(msg, user)

			if user in self.messages:
				self.messages[user].append([None, msg])
			else:
				self.messages[user] = [[None, msg]]

			lab = Label(text=msg, size_hint_y=None, color=(1, 1, 1, 1), markup=True, halign='right')
			lab.bind(width=lambda s, w:
				s.setter('text_size')(s, (w, None)))
			lab.bind(texture_size=lab.setter('size'))

			with lab.canvas.before:
				Color(.67, .82, 1, mode='hsv')
				lab.bg_rect = Rectangle(pos=self.pos, size=self.size)

			lab.bind(pos=redraw, size=redraw)
			self.sub_layout.add_widget(lab)
			self.reply.text = ""

			if self.new:
				self.sub_layout.remove_widget(self.new_lab)
				self.new = False

	def name_to_bg(self, data):
		is_str = lambda obj: issubclass(obj.__class__, str)
		poly = 0x1021
		reg = 0x0000

		if is_str(data):
			data = list(map(ord, data))
		elif is_bytes(data):
			data = list(data)

		data.append(0)
		data.append(0)

		for byte in data:
			mask = 0x80
			while mask > 0:
				reg <<= 1
				if byte & mask:
					reg += 1
				mask >>= 1
				if reg > 0xffff:
					reg &= 0xffff
					reg ^= poly

		print(reg)
		rem = reg % 360
		print(rem)
		rem = float(rem)
		rem = rem/360
		print(rem)
		return rem

	def name_to_txt(self, data):
		rem = self.name_to_bg(data)
		dis = rem + 0.5

		if dis > 1:
			dis = dis - 1

		print(dis)
		return dis
