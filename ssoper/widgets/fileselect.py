# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

import json
import os

from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder

Builder.load_string("""
<FileWidget@BoxLayout>:
	id: file_layout
	FileChooserListView:
		id: filechooser
		on_selection: file_layout.open(filechooser.path, filechooser.selection)
""")


class FileWidget(BoxLayout):
	def __init__(self, *args, **kwargs):
		super(FileWidget, self).__init__(*args, **kwargs)
		self.data = None
		self.true_path = None

	def open(self, path, filename):
		"""
		Load the .json from the selected path.

		:param str path: The directory of the file.
		:param str filename: The name of the file.
		:rtype: JSON object.
		:return: The opened JSON file.
		"""
		with open(os.path.join(path, filename[0])) as f:
			path_list = str(f).split("'")
			self.true_path = path_list[1]
		return self.true_path
