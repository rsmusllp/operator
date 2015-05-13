#!/usr/bin/env python

import logging

from kivy.uix.boxlayout import BoxLayout

class TopLevel(BoxLayout):
	def __init__(self, *args, **kwargs):
		self.logger = logging.getLogger("kivy.operator.{0}".format(self.__class__.__name__))
		super(TopLevel, self).__init__(*args, **kwargs)