# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

import re
import pprint
import json
import os

from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.storage.jsonstore import JsonStore
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
        self.dataP = None

    def open(self, path, filename):
        #Load the .JSON from the selected path
        with open(os.path.join(path, filename[0])) as f:
            path_list = str(f).split("'")
            true_path = path_list[1]
            with open(true_path) as p:
                self.dataP = json.load(p)
        return self.dataP