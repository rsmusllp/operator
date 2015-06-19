# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

import functools
import glob
import json
import os
import re
import shutil
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
from kivy.properties import ObjectProperty
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle

from ssoper.widgets.fileselect import FileWidget

from third_party.kivy_toaster.src.toast.androidtoast import toast


class ChecklistWidget(ScrollView):
	screen_manager = ObjectProperty(None)
	def __init__(self, *args, **kwargs):
		super(ChecklistWidget, self).__init__(*args, **kwargs)
		Window.bind(on_keyboard=self.on_back_btn)
		self.checklist_layout = GridLayout(cols=1)
		self.json_p = ""
		self.title = ""
		self.submit_button = Button()
		self.filewidget = FileWidget()
		self.confirmation_popup = Popup()
		self.loading_message_popup = Popup()
		self.data = None
		self.result = []
		self.question_list = []
		self.response_list = []
		self.user_response = False
		self.alive = False
		self.checklist_menu_layout = GridLayout(cols=1)
		self.file_select_popup = Popup()
		self.set_background(self.checklist_menu_layout)
		self.do_get_checklists()

	def set_background(self, layout):
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

	def do_get_checklists(self):
		"""
		Creates the base screen for the checklist manager.
		It includes previously loaded checklists as well as a button for new checklists.
		"""
		self.clear_widgets()
		self.checklist_menu_layout.clear_widgets()
		titles = []
		new_json_button = Button(text="Load new checklist", size_hint_y=None)
		new_json_button.bind(on_release=lambda x: self.do_popup_file_select())
		self.checklist_menu_layout.add_widget(new_json_button)
		for dirname, dirnames, _ in os.walk('/sdcard/operator/checklists/'):
			for subdirname in dirnames:
				loc = os.path.join(dirname, subdirname)
				name = loc.split("/")
				titles.append(name[len(name)-1])
		for title in titles:
			button_to_checklist = Button(text=title, size_hint_y=None)
			button_to_checklist.bind(on_release=functools.partial(self.do_open_checklist, title))
			self.checklist_menu_layout.add_widget(button_to_checklist)
		self.add_widget(self.checklist_menu_layout)

	def do_popup_file_select(self):
		"""
		Prompts the user to navigate to the .JSON file
		"""
		self.filewidget = FileWidget()
		box = BoxLayout(orientation='vertical')
		box_int = BoxLayout(orientation='horizontal', size_hint=(1, .2))
		close_button = Button(text='Load')
		close_button.bind(on_release=lambda x: self.do_add_checklist_location())
		dismiss_button = Button(text='Cancel')
		dismiss_button.bind(on_release=lambda x: self.file_select_popup.dismiss())
		box.clear_widgets()
		box_int.add_widget(close_button)
		box_int.add_widget(dismiss_button)
		box.add_widget(self.filewidget)
		box.add_widget(box_int)
		self.file_select_popup = Popup(title='Choose File', content=box, size_hint=(None, None), size=(800, 1000), auto_dismiss=False)
		self.file_select_popup.open()

	def do_load_true_path(self, path, filename):
		try:
			if path is not None and filename is not None:
				with open(os.path.join(path, filename[0])) as f:
					path_list = str(f).split("'")
					self.true_path = path_list[1]
				return self.true_path
		except(IOError, IndexError):
			pass

	def do_add_checklist_location(self):
		"""
		Creates the subdirectory for the checklist.
		"""
		path = self.do_load_true_path(self.filewidget.path, self.filewidget.filename)
		if path is not None and '.json' in str(path):
			with open(path) as p:
				self.data = json.load(p)
			title = 'checklist_name_not_found'
			for line in self.data:
				if line == 'checklist_title':
					title = self.data[line]['title']
			d = "/sdcard/operator/checklists/"+title
			if not os.path.exists(d):
				os.makedirs(d)
			open(d+"/"+title+"_template.json", 'a')
			shutil.copyfile(str(path), d+"/"+title+"_template.json")
			self.do_get_checklists()
			self.file_select_popup.dismiss()
		else:
			toast("Not a valid file!", True)

	def do_open_checklist(self, title, event):
		"""
		Opens the checklist, depending on the request from the user in the base menu.

		:param str title: The title of the checklist, according to the title field in the .JSON file.
		"""
		self.clear_widgets()
		self.json_p = self.get_recent_json(title)
		self.title = title
		self.gen_checklist()

	def get_recent_json(self, title):
		"""
		Load the most recent .JSON file in the subdirectory.

		:param str title: The title of the checklist, according to the title field in the .JSON file.
		"""
		newest = max(glob.iglob(os.path.join('/sdcard/operator/checklists/'+title, '*.[Jj][Ss][Oo][Nn]')), key=os.path.getctime)
		return newest

	def on_back_btn(self, window, key, *args):
		"""
		Saves when back button is called.
		"""
		if key == 27:
			self.submit_button.trigger_action(duration=0)

	def gen_checklist(self):
		"""
		Generates the actual layout, based on the parsed .JSON
		"""
		self.checklist_layout.size_hint_y = None
		self.checklist_layout.id = 'checklist'
		self.checklist_layout.bind(minimum_height=self.checklist_layout.setter('height'))
		path = self.json_p
		self.checklist_layout.clear_widgets()
		if path is not None and '.json' in str(path):
			with open(path) as p:
				self.data = json.load(p)
			self.result = self.decode_json(self.data)
			self.question_list = self.result[0]
			self.response_list = self.result[1]
			answers = self.result[2]
			for i in range(len(self.question_list)):
				# Adds a Label for each question
				self.checklist_layout.add_widget(Label(text=str(self.question_list[i]), id='Question ' + str(i), size_hint_y=None))
				if self.response_list[i] == 'N':
					# Numerical input only
					float_input = FloatInput(hint_text=str(self.question_list[i]), id='Response ' + str(i), size_hint_y=None)
					if answers[i]:
						float_input.text = answers[i]
					self.checklist_layout.add_widget(float_input)
				elif self.response_list[i] == 'T':
					# Text input
					text_input = TextInput(hint_text=str(self.question_list[i]), id='Response ' + str(i), size_hint_y=None)
					if answers[i]:
						text_input.text = answers[i]
					self.checklist_layout.add_widget(text_input)
				elif self.response_list[i] == 'Y':
					# Yes/No radio buttons
					yes_no_responses = BoxLayout(orientation='vertical', id='Response ' + str(i), size_hint_y=None)
					yes_response = BoxLayout(orientation='horizontal', id='sub Response' + str(i))
					yes_response.add_widget(Label(text='Yes', id='Response ' + str(i)))
					yes_checkbox = CheckBox(id='Response ' + str(i), group='yes_no' + str(i))
					if answers[i][0]:
						yes_checkbox.active = True
					yes_response.add_widget(yes_checkbox)
					no_response = BoxLayout(orientation='horizontal', id='sub Response' + str(i))
					no_response.add_widget(Label(text='No', id='Response ' + str(i)))
					no_checkbox = CheckBox(id='Response ' + str(i), group='yes_no' + str(i))
					if answers[i][1]:
						no_checkbox.active = True
					no_response.add_widget(no_checkbox)
					yes_no_responses.add_widget(yes_response)
					yes_no_responses.add_widget(no_response)
					self.checklist_layout.add_widget(yes_no_responses)
				elif self.response_list[i] == 'C':
					# Checkboxes with support for 'Other' option
					multiple_responses = BoxLayout(orientation='vertical', id='Response ' + str(i), size_hint_y=None, height=150)
					j = 0
					while j < len(answers[i][0]):
						response = BoxLayout(orientation='horizontal', id='sub Response ' + str(i))
						response.add_widget(Label(text=str(answers[i][0][j]), id='Response ' + str(i)))
						if isinstance(answers[i][0][j], unicode):
							if 'Other' in answers[i][0][j]:
								response.padding = [20, 0, 73, 0]
								text_input = TextInput(id='Response ' + str(i) + 'Other', size_hint_x=.8)
								try:
									text_input.text = answers[i][0][j+1]
									response.add_widget(text_input)
									check_box = CheckBox(id='Response ' + str(i))
									check_box.active = answers[i][1][j]
								except IndexError:
									text_input.text = ''
									check_box = CheckBox(id='Response ' + str(i))
									check_box.active = False
								response.add_widget(check_box)
								multiple_responses.add_widget(response)
								break
						check_box = CheckBox(id='Response ' + str(i))
						try:
							if answers[i][1][j]:
								check_box.active = True
						except IndexError:
							pass
						j += 1
						response.add_widget(check_box)
						multiple_responses.add_widget(response)
					self.checklist_layout.add_widget(multiple_responses)
				elif self.response_list[i] == 'D':
					# Date spinners for month, day and year
					date_response = BoxLayout(orientation='horizontal', id='Response ' + str(i), size_hint_y=None)
					month_values = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
					month_spinner = Spinner(
						id='Response ' + str(i),
						text=answers[i][0],
						values=month_values)
					day_values = []
					for j in range(1, 32):
						day_values.append("{0:02}".format(j))
					day_spinner = Spinner(
						id='Response ' + str(i),
						text=answers[i][1],
						values=day_values)
					year_values = []
					for j in range(2015, 1900, -1):
						year_values.append(str(j))
					year_spinner = Spinner(
						id='Response ' + str(i),
						text=answers[i][2],
						values=year_values)
					date_response.add_widget(month_spinner)
					date_response.add_widget(day_spinner)
					date_response.add_widget(year_spinner)
					self.checklist_layout.add_widget(date_response)
			clear_and_delete = BoxLayout(orientation='horizontal', id='clear_and_delete', size_hint_y=None)
			clear_button = Button(
				text='Clear',
				id='clear')
			delete_button = Button(
				text='Delete',
				id='delete')
			clear_button.bind(on_release=lambda x: self.do_confirm_action("clear"))
			delete_button.bind(on_release=lambda x: self.do_confirm_action("delete"))
			clear_and_delete.add_widget(clear_button)
			clear_and_delete.add_widget(delete_button)
			self.checklist_layout.add_widget(clear_and_delete)
			self.submit_button = Button(
				text='Save',
				id='submit',
				size_hint_y=None)
			self.submit_button.bind(on_release=self.do_store_data)
			self.checklist_layout.add_widget(self.submit_button)
			self.clear_widgets()
			self.set_background(self.checklist_layout)
			self.add_widget(self.checklist_layout)
			self.loading_message_popup.dismiss()
			self.alive = True

	def do_store_data(self, event):
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
		json_filename = time.strftime('%H:%M_%m-%d-%Y') + '.json'
		file_location = '/sdcard/operator/checklists/' + self.title + "/" + json_filename
		d = os.path.dirname(file_location)
		if not os.path.exists(d):
			os.makedirs(d)
		store = JsonStore(file_location)
		store.put('checklist_title', title=self.title)
		for i in range(len(questions)):
			store.put('q'+ str(i), question=questions[i], answer=answers[i], response_type=self.response_list[i])
		self.clear_widgets()
		self.do_get_checklists()

	def decode_json(self, json_data):
		"""
		Parse through the .JSON input

		:param json_data: JSON file.
		:rtype: array
		:return: An array of three arrays containing strings
		"""
		qs = []
		title = ''
		for line in json_data:
			if line == 'checklist_title':
				title = json_data[line]['title']
			else:
				qs.append(line)
		qs_in_order = [0]*len(qs)
		for element in qs:
			number = int(element[1:])
			qs_in_order[number] = element
		questions = []
		for q in qs_in_order:
			questions.append(json_data[q]['question'])
		response_types = []
		for q in qs_in_order:
			response_types.append(json_data[q]['response_type'])
		answers = [0]*len(qs_in_order)
		for i in range(len(response_types)):
			if response_types[i] == 'C':
				answers[i] = []
				answers[i].append([])
				answers[i].append([])
				j = 0
				while j < len(json_data[qs_in_order[i]]['answer']):
					answers[i][0].append(json_data[qs_in_order[i]]['answer'][j])
					try:
						if isinstance(json_data[qs_in_order[i]]['answer'][j], unicode):
							if 'Other' in json_data[qs_in_order[i]]['answer'][j]:
								try:
									answers[i][0].append(json_data[qs_in_order[i]]['answer'][j+1])
									answers[i][1].append(json_data[qs_in_order[i]]['answer'][j+2])
								except IndexError:
									answers[i][1].append(False)
									answers[i][0].append('')
								break
							elif isinstance(json_data[qs_in_order[i]]['answer'][j+1], bool):
								answers[i][1].append(json_data[qs_in_order[i]]['answer'][j+1])
								j += 1
						j += 1
					except IndexError:
						answers[i][1].append(False)
						j += 1
			elif response_types[i] == 'T':
				try:
					answers[i] = json_data[qs_in_order[i]]['answer']
				except (IndexError, KeyError):
					answers[i] = ''
			elif response_types[i] == 'N':
				try:
					answers[i] = json_data[qs_in_order[i]]['answer']
				except (IndexError, KeyError):
					answers[i] = 0
			elif response_types[i] == 'D':
				answers[i] = []
				try:
					for j in json_data[qs_in_order[i]]['answer']:
						answers[i].append(j)
				except (IndexError, KeyError):
					answers[i] = ['January', '01', '2015']
			elif response_types[i] == 'Y':
				try:
					answers[i] = []
					answers[i].append(json_data[qs_in_order[i]]['answer'][1])
					answers[i].append(json_data[qs_in_order[i]]['answer'][3])
				except (IndexError, KeyError):
					answers[i] = []
					answers[i].append(False)
					answers[i].append(False)
		result = [questions, response_types, answers, title]
		return result

	def do_confirm_action(self, method):
		"""
		This function will generate a popup that prompts the user to confirm their decision.

		:param str method: String to indicate the type of action.
		:rtype: bool
		:return: Returns a boolean. If true, the action is confirmed.
		"""
		confirmation_box = BoxLayout(orientation='vertical')
		confirmation_box.add_widget(Label(text='Are you sure?\nThis action is permanent.'))
		affirm_and_neg = BoxLayout(orientation='horizontal')
		affirmative = Button(text='Yes')
		negative = Button(text='Cancel')
		if method == "clear":
			affirmative.bind(on_release=lambda x: self.do_set_response(True, "clear"))
			negative.bind(on_release=lambda x: self.do_set_response(False, "clear"))
		else:
			affirmative.bind(on_release=lambda x: self.do_set_response(True, "delete"))
			negative.bind(on_release=lambda x: self.do_set_response(False, "delete"))
		affirm_and_neg.add_widget(affirmative)
		affirm_and_neg.add_widget(negative)
		confirmation_box.add_widget(affirm_and_neg)
		self.confirmation_popup = Popup(title='Confirmation', content=confirmation_box, size_hint=(None, None), size=(500, 500), auto_dismiss=False)
		self.confirmation_popup.open()

	def do_set_response(self, response, method):
		"""
		Calls the appropriate method after being confirmed. If not confirmed, the popup is dismissed with no action taken.

		:param bool response: Boolean to confirm response.
		:param str method: String to confrim the type of action.
		"""
		self.user_response = response
		if method == "clear" and response:
			self.do_clear_data()
		elif method == "delete" and response:
			self.do_delete_data()
		self.confirmation_popup.dismiss()

	def do_clear_data(self):
		"""
		Clears all responses of the current checklist. This does not delete the checklist.
		"""
		for child in self.checklist_layout.walk():
			if isinstance(child, TextInput) or isinstance(child, FloatInput):
				child.text = ''
			elif isinstance(child, Spinner):
				if 'day' in child.id:
					child.text = '01'
				elif 'month' in child.id:
					child.text = 'January'
				elif 'year' in child.id:
					child.text = '2015'
			elif isinstance(child, CheckBox):
				child.active = False

	def do_delete_data(self):
		shutil.rmtree('/sdcard/operator/checklists/' + self.title)
		self.clear_widgets()
		self.do_get_checklists()

class FloatInput(TextInput):
	"""
	Text field that restricts input to numbers.
	"""
	pat = re.compile('[^0-9]')
	def insert_text(self, substring, from_undo=False):
		pat = self.pat
		if '.' in self.text:
			s = re.sub(pat, '', substring)
		else:
			s = '.'.join([re.sub(pat, '', s) for s in substring.split('.', 1)])
		return super(FloatInput, self).insert_text(s, from_undo=from_undo)
