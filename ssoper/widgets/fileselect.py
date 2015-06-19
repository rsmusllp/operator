# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

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
		self.path = None
		self.filename = None

	def open(self, path, filename):
		"""
		Load the .json from the selected path.

		:param str path: The directory of the file.
		:param array filename: The name of the file.
		"""

		self.path = path
		self.filename = filename
