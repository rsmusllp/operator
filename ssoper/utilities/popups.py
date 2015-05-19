# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

from kivy.uix.label import Label
from kivy.uix.popup import Popup


def popup_error(popup_title, popup_content):

	content_label = Label(text=popup_content)
	error_popup = Popup(title=popup_title, content=content_label, separator_color=[255 / 255., 0 / 255., 0 / 255., 1.], size_hint=(1,.2))
	error_popup.open()

def popup_good(popup_title, popup_content):

	content_label = Label(text=popup_content)
	good_popup = Popup(title=popup_title, content=content_label, separator_color=[0 / 255., 255 / 255., 0 / 255., 1.], size_hint=(1,.2))
	good_popup.open()

def popup_msg(popup_title, popup_content):

	content_label = Label(text=popup_content)
	msg_popup = Popup(title=popup_title, content=content_label, separator_color=[96 / 255., 96 / 255., 96 / 255., 1.], size_hint=(1,.2))
	msg_popup.open()

def popup_warn(popup_title, popup_content):

	content_label = Label(text=popup_content)
	warn_popup = Popup(title=popup_title, content=content_label, separator_color=[255 / 255., 255 / 255., 0 / 255., 1.], size_hint=(1,.2))
	warn_popup.open()
