# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

import re
import time

from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.storage.jsonstore import JsonStore
from kivy.uix.popup import Popup

from fileselect import FileWidget


class ChecklistWidget(ScrollView):

	def __init__(self, *args, **kwargs):
		super(ChecklistWidget, self).__init__(*args, **kwargs)
		self.checklist_layout = GridLayout(cols=1)
		self.filewidget = FileWidget()
		self.popup = Popup()
		self.data = None
		self.result = []
		self.question_list = []
		self.response_list = []
		self.do_load_file()

	def do_load_file(self):
		"""
		Initial state where nothing has been loaded yet, just sets the framework for something to load.
		"""
		self.checklist_layout.size_hint_y = None
		self.checklist_layout.id = 'checklist'
		self.checklist_layout.bind(minimum_height=self.checklist_layout.setter('height'))
		json_button = Button(text='Load Json')
		json_button.bind(on_release=lambda x: self.do_popup())
		self.checklist_layout.add_widget(json_button)
		self.add_widget(self.checklist_layout)

	def do_popup(self):
		"""
		Prompts the user to navigate to the .JSON file
		"""
		box = BoxLayout()
		close_button = Button(text='Load')
		close_button.bind(on_release=lambda x: self.gen_checklist())
		box.add_widget(close_button)
		box.add_widget(self.filewidget)
		self.popup = Popup(title='Choose File', content=box, size_hint=(None, None), size=(600, 600), auto_dismiss=False)
		self.popup.open()

	def gen_checklist(self):
		"""
		Generates the actual layout, based on the parsed .JSON
		"""
		self.data = self.filewidget.data
		self.result = self.decode_json(self.data)
		self.question_list = self.result[0]
		self.response_list = self.result[1]
		options = self.result[2]
		for i in range(len(self.question_list)):
			#Adds a Label for each question
			self.checklist_layout.add_widget(Label(text=str(self.question_list[i]), id='Question ' + str(i), size_hint_y=None))
			if self.response_list[i] == 'N':
				#Numerical input only
				self.checklist_layout.add_widget(FloatInput(hint_text=str(self.question_list[i]), id='Response ' + str(i), size_hint_y=None))
			elif self.response_list[i] == 'T':
				#text input
				self.checklist_layout.add_widget(TextInput(hint_text=str(self.question_list[i]), id='Response ' + str(i), size_hint_y=None))
			elif self.response_list[i] == 'Y':
				#Yes/No radio buttons
				yes_no_responses = BoxLayout(orientation='vertical', id='Response ' + str(i), size_hint_y=None)
				yes_response = BoxLayout(orientation='horizontal', id='sub Response' + str(i))
				yes_response.add_widget(Label(text='Yes', id='Response ' + str(i)))
				yes_response.add_widget(CheckBox(id='Response ' + str(i), group='yes_no' + str(i)))
				no_response = BoxLayout(orientation='horizontal', id='sub Response' + str(i))
				no_response.add_widget(Label(text='No', id='Response ' + str(i)))
				no_response.add_widget(CheckBox(id='Response ' + str(i), group='yes_no' + str(i)))
				yes_no_responses.add_widget(yes_response)
				yes_no_responses.add_widget(no_response)
				self.checklist_layout.add_widget(yes_no_responses)
			elif self.response_list[i] == 'C':
				#Checkboxes with support for 'Other' option
				multiple_responses = BoxLayout(orientation='vertical', id='Response ' + str(i), size_hint_y=None, height=100)
				for j in range(len(options[i])):
					response = BoxLayout(orientation='horizontal', id='sub Response ' + str(i))
					response.add_widget(Label(text=str(options[i][j]), id='Response ' + str(i)))
					if 'Other' in options[i][j]:
						response.padding = [20, 0, 73, 0]
						response.add_widget(TextInput(id='Response ' + str(i) + 'Other', size_hint_x=.8, ))
					response.add_widget(CheckBox(id='Response ' + str(i)))
					multiple_responses.add_widget(response)
				self.checklist_layout.add_widget(multiple_responses)
			elif self.response_list[i] == 'D':
				#Date spinners for month, day and year
				date_response = BoxLayout(orientation='horizontal', id='Response ' + str(i), size_hint_y=None)
				month_values = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
				month_spinner = Spinner(
					id='Response ' + str(i),
					text='January',
					values=month_values)
				day_values = []
				for j in range(1, 32):
					day_values.append("{0:02}".format(j))
				day_spinner = Spinner(
					id='Response ' + str(i),
					text='01',
					values=day_values)
				year_values = []
				for j in range(2015, 1900, -1):
					year_values.append(str(j))
				year_spinner = Spinner(
					id='Response ' + str(i),
					text='2015',
					values=year_values)
				date_response.add_widget(month_spinner)
				date_response.add_widget(day_spinner)
				date_response.add_widget(year_spinner)
				self.checklist_layout.add_widget(date_response)
		submit_button = Button(
			text='Submit',
			id='submit',
			size_hint_y=None)
		submit_button.bind(on_release=self.do_store_data)
		self.checklist_layout.add_widget(submit_button)
		self.clear_widgets()
		self.add_widget(self.checklist_layout)
		self.popup.dismiss()

	def do_store_data(self):
		"""
		Reads each response and writes a .JSON file with questions and responses.
		"""
		questions = self.question_list
		answers = []
		for child in self.checklist_layout.walk(loopback=False):
			if isinstance(child, FloatInput):
				answers.append(child.text)
			elif isinstance(child, BoxLayout) and child.id:
				temp_responses = []
				for grandchild in child.walk(restrict=True):
					if grandchild.id:
						if child.id in grandchild.id and not 'sub' in grandchild.id:
							if isinstance(grandchild, CheckBox):
								temp_responses.append(grandchild.active)
							elif not isinstance(grandchild, BoxLayout):
								temp_responses.append(grandchild.text)
				if temp_responses:
					answers.append(temp_responses)
			elif isinstance(child, TextInput) and not 'Other' in child.id:
				answers.append(child.text)
		json_filename = time.strftime('%Y-%m-%d-%H-%M-%S') + '.json'
		store = JsonStore('/storage/sdcard/' + json_filename)
		for i in range(len(questions)):
			store.put('q'+ str(i), question=questions[i], answer=answers[i])

	def decode_json(self, json_data):
		"""
		Parse through the .JSON input

		:param: JSON file.
		:rtype: array
		:return: An array of three arrays containing strings
		"""
		qs = []
		for line in json_data:
			qs.append(line)
		qs_in_order = [0]*len(qs)
		for element in qs:
			number = int(element[1:])
			qs_in_order[number] = element
		questions = []
		for q in qs_in_order:
			questions.append(json_data[q]['id'])
		response_types = []
		for q in qs_in_order:
			response_types.append(json_data[q]['response_type'])
		options_for_answer = [0]*len(qs_in_order)
		for i in range(len(response_types)):
			if response_types[i] == 'C':
				options_for_answer[i] = json_data[qs_in_order[i]]['options']
		result = [questions, response_types, options_for_answer]
		return result

class FloatInput(TextInput):
	#Restricts input to numbers
	pat = re.compile('[^0-9]')
	def insert_text(self, substring, from_undo=False):
		pat = self.pat
		if '.' in self.text:
			s = re.sub(pat, '', substring)
		else:
			s = '.'.join([re.sub(pat, '', s) for s in substring.split('.', 1)])
		return super(FloatInput, self).insert_text(s, from_undo=from_undo)
