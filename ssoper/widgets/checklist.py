# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

import collections
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
from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle

from ssoper.widgets.fileselect import FileWidget

from third_party.kivy_toaster.src.toast.androidtoast import toast

DEFAULT_CHECKLIST_NAME = 'Operator Checklist'
MONTHS = ('January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December')

ChecklistQuestion = collections.namedtuple('ChecklistQuestion', ('question', 'type', 'answer'))
ChecklistResponse = collections.namedtuple('ChecklistResponse', ('question', 'label_widget', 'response_widget'))

class ChecklistWidget(ScrollView):
	screen_manager = ObjectProperty(None)
	def __init__(self, *args, **kwargs):
		super(ChecklistWidget, self).__init__(*args, **kwargs)
		Window.bind(on_keyboard=self.on_back_btn)
		self.checklist_layout = GridLayout(cols=1)
		self.checklist_layout.size_hint_y = None
		self.checklist_layout.id = 'checklist'
		self.checklist_layout.bind(minimum_height=self.checklist_layout.setter('height'))
		self.title = ''
		self.submit_button = Button()
		self.filewidget = FileWidget()
		self.confirmation_popup = Popup()
		self.data = None
		self.question_list = []
		self.response_list = []
		self.rect = Rectangle()
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
		new_json_button = Button(text='Load New Checklist', size_hint_y=None)
		new_json_button.bind(on_release=lambda x: self.do_popup_file_select())
		self.checklist_menu_layout.add_widget(new_json_button)
		for dirname, dirnames, _ in os.walk('/sdcard/operator/checklists/'):
			for subdirname in dirnames:
				loc = os.path.join(dirname, subdirname)
				name = loc.split("/")
				titles.append(name[len(name) - 1])
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
		"""
		Does a series of a checks to make sure the file that is trying to be loaded is valid.

		:param str path: The directory of the file.
		:param list filename: The name of the file.
		:return: The path to the validated JSON file. If the path is deemed invalid, None is returned.
		:rtype: str
		"""
		full_path = os.path.join(path, filename[0])
		if not os.path.isfile(full_path):
			toast("Not a valid file!", True)
			return
		if not os.access(full_path, (os.R_OK | os.W_OK)):
			toast("No permission, please move file", True)
			return
		if not full_path.endswith('.json'):
			toast("Not a JSON file!", True)
			return
		with open(full_path) as f:
			path_list = str(f).split("'")
			true_path = path_list[1]
		if not os.path.exists(true_path):
			toast("Not a valid path!", True)
		return true_path

	def do_add_checklist_location(self):
		"""
		Creates the subdirectory for the checklist.
		"""
		path = self.do_load_true_path(self.filewidget.path, self.filewidget.filename)
		if not isinstance(path, str):
			return
		with open(path) as p:
			self.data = json.load(p)
		title = self.data.get('title', DEFAULT_CHECKLIST_NAME)
		d = os.path.join('/sdcard/operator/checklists/', title)
		if not os.path.exists(d):
			os.makedirs(d)
		open(os.path.join(d, title + '_template.json'), 'a')
		shutil.copyfile(path, os.path.join(d, title + '_template.json'))
		self.do_get_checklists()
		self.file_select_popup.dismiss()

	def do_open_checklist(self, title, event):
		"""
		Opens the checklist, depending on the request from the user in the base menu.

		:param str title: The title of the checklist, according to the title field in the .JSON file.
		"""
		toast("Loading...", True)
		self.clear_widgets()
		self.title = title
		json_path = self.get_recent_json(title)
		if json_path:
			self.gen_checklist(json_path)

	def get_recent_json(self, title):
		"""
		Load the most recent .JSON file in the subdirectory.

		:param str title: The title of the checklist, according to the title field in the .JSON file.
		"""
		newest = max(glob.iglob(os.path.join('/sdcard/operator/checklists', title, '*.[Jj][Ss][Oo][Nn]')), key=os.path.getctime)
		return newest

	def on_back_btn(self, window, key, *args):
		"""
		Saves when back button is called.
		"""
		if key == 27:
			self.submit_button.trigger_action(duration=0)

	def _get_checklist_widget_check(self, question, i):
		multiple_responses = BoxLayout(orientation='vertical', id='Response ' + i, size_hint_y=None, height=150)
		for key, value in question.answer.items():
			response = BoxLayout(orientation='horizontal', id='sub Response ' + i)
			response.add_widget(Label(text=key, id=key))
			if key.lower().startswith('other'):
				response.padding = (20, 0, 73, 0)
				widget = TextInput(id=key, size_hint_x=.8)
				if isinstance(value, (str, unicode)):
					widget.text = value
			else:
				widget = CheckBox(id=key)
				widget.active = value
			response.add_widget(widget)
			multiple_responses.add_widget(response)
		return multiple_responses

	def _get_checklist_widget_response_check(self, widget):
		results = {}
		for child in widget.walk(restrict=True):
			if isinstance(child, TextInput):
				value = child.text
			elif isinstance(child, CheckBox):
				value = child.active
			else:
				continue
			results[child.id] = value
		return results

	def _get_checklist_widget_date(self, question, i):
		date_widget = BoxLayout(orientation='horizontal', id='Response ' + i, size_hint_y=None)
		month_spinner = Spinner(id='Month Response ' + i, text=question.answer[0], values=MONTHS)
		day_spinner = Spinner(id='Day Response ' + i, text=question.answer[1], values=["{0:02}".format(j) for j in range(1, 32)])
		year_spinner = Spinner(id='Year Response ' + i, text=question.answer[2], values=["{0:04}".format(j) for j in range(2100, 1900, -1)])
		date_widget.add_widget(month_spinner)
		date_widget.add_widget(day_spinner)
		date_widget.add_widget(year_spinner)
		return date_widget

	def _get_checklist_widget_response_date(self, widget):
		for child in widget.children:
			if 'Month' in child.id:
				month = child.text
			elif 'Day' in child.id:
				day = child.text
			elif 'Year' in child.id:
				year = child.text
		return (month, day, year)

	def _get_checklist_widget_num(self, question, i):
		float_widget = FloatInput(hint_text=question.question, id='Response ' + i, size_hint_y=None)
		float_widget.text = str(question.answer)
		return float_widget

	def _get_checklist_widget_response_num(self, widget):
		return float(widget.text)

	def _get_checklist_widget_text(self, question, i):
		text_widget = TextInput(hint_text=question.question, id='Response ' + i, size_hint_y=None)
		text_widget.text = question.answer
		return text_widget

	def _get_checklist_widget_response_text(self, widget):
		return widget.text

	def _get_checklist_widget_yes_no(self, question, i):
		yes_no_widget = BoxLayout(orientation='vertical', id='Response ' + i, size_hint_y=None)
		yes_response = BoxLayout(orientation='horizontal', id='sub Response' + i)
		yes_response.add_widget(Label(text='Yes', id='Response ' + i))
		yes_checkbox = CheckBox(id='Yes Response ' + i, group='yes_no' + i)
		yes_response.add_widget(yes_checkbox)
		no_response = BoxLayout(orientation='horizontal', id='sub Response' + i)
		no_response.add_widget(Label(text='No', id='Response ' + i))
		no_checkbox = CheckBox(id='No Response ' + i, group='yes_no' + i)
		no_response.add_widget(no_checkbox)
		if question.answer:
			yes_checkbox.active = True
		else:
			no_checkbox.active = True
		yes_no_widget.add_widget(yes_response)
		yes_no_widget.add_widget(no_response)
		return yes_no_widget

	def _get_checklist_widget_response_yes_no(self, widget):
		for child in widget.children:
			for child2 in child.children:
				if isinstance(child2, CheckBox):
					if 'Yes' in child2.id:
						return bool(child2.active)
					else:
						return not bool(child2.active)

	def gen_checklist(self, json_path):
		"""
		Generates the actual layout, based on the parsed .JSON

		:param str json_path: The path to the JSON checklist file to load.
		"""
		self.checklist_layout.clear_widgets()
		with open(json_path) as file_h:
			self.data = json.load(file_h)
		self.question_list = self.decode_json(self.data)
		self.response_list = []
		for i, question in enumerate(self.question_list):
			i = str(i)
			widget_handler = getattr(self, '_get_checklist_widget_' + question.type, None)
			if widget_handler:
				# Adds a Label for each question
				response = ChecklistResponse(
					question=question,
					label_widget=Label(text=question.question, id='Question ' + i, size_hint_y=None),
					response_widget=widget_handler(question, i)
				)
				self.checklist_layout.add_widget(response.label_widget)
				self.checklist_layout.add_widget(response.response_widget)
				self.response_list.append(response)
		clear_and_delete = BoxLayout(orientation='horizontal', id='clear_and_delete', size_hint_y=None)
		clear_button = Button(text='Clear', id='clear')
		delete_button = Button(text='Delete', id='delete')
		clear_button.bind(on_release=lambda x: self.do_confirm_action('clear'))
		delete_button.bind(on_release=lambda x: self.do_confirm_action('delete'))
		clear_and_delete.add_widget(clear_button)
		clear_and_delete.add_widget(delete_button)
		self.checklist_layout.add_widget(clear_and_delete)
		self.submit_button = Button(text='Save', id='submit', size_hint_y=None)
		self.submit_button.bind(on_release=self.do_store_data)
		self.checklist_layout.add_widget(self.submit_button)
		self.clear_widgets()
		self.set_background(self.checklist_layout)
		self.add_widget(self.checklist_layout)

	def do_store_data(self, event):
		"""
		Reads each response and writes a .JSON file with questions and responses.
		"""
		store = []
		answer = None
		for response in self.response_list:
			question = response.question
			widget = response.response_widget
			widget_handler = getattr(self, '_get_checklist_widget_response_' + question.type, None)
			if widget_handler:
				answer = widget_handler(widget)
			store.append(ChecklistQuestion(
				question=question.question,
				type=question.type,
				answer=answer
			)._asdict())

		json_filename = time.strftime('%H:%M_%m-%d-%Y') + '.json'
		file_location = os.path.join('/sdcard/operator/checklists', self.title)
		if not os.path.exists(file_location):
			os.makedirs(file_location)
		store = dict(title=self.title, questions=store)
		with open(os.path.join(file_location, json_filename), 'w') as file_h:
			json.dump(store, file_h, sort_keys=True, indent=2, separators=(',', ': '))
		self.clear_widgets()
		self.do_get_checklists()

	def decode_json(self, json_data):
		"""
		Parse through the .JSON input

		:param json_data: JSON file.
		:rtype: list
		:return: An list of three arrays containing strings
		"""
		questions = []
		for question in json_data.get('questions', []):
			if not 'question' in question:
				continue
			q_type = question.get('type', 'text')
			q_answer = question.get('answer')
			if q_answer is None:
				q_answer = {'check': {}, 'date': ('January', '01', '2015'), 'num': 0, 'text': '', 'yes_no': False}[q_type]
				if isinstance(q_answer, dict) and len(q_answer) == 0:
					for opt in question.get('options', []):
						q_answer[opt] = False
			questions.append(ChecklistQuestion(
				question=question['question'],
				type=q_type,
				answer=q_answer
			))
		return questions

	def do_confirm_action(self, method):
		"""
		This function will generate a popup that prompts the user to confirm their decision.

		:param str method: String to indicate the type of action.
		:rtype: bool
		:return: Returns a boolean. If true, the action is confirmed.
		"""
		confirmation_box = BoxLayout(orientation='vertical')
		confirmation_box.add_widget(Label(text='Are you sure?\nThis action is permanent.'))
		affirm_and_neg = BoxLayout(orientation='horizontal', spacing=50)
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
		self.confirmation_popup = Popup(title='Confirmation', content=confirmation_box, size_hint=(.7, None), size=(650, 500), auto_dismiss=False)
		self.confirmation_popup.open()

	def do_set_response(self, response, method):
		"""
		Calls the appropriate method after being confirmed. If not confirmed, the popup is dismissed with no action taken.

		:param bool response: Boolean to confirm response.
		:param str method: String to confirm the type of action.
		"""
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
			if isinstance(child, (TextInput, FloatInput)):
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
		"""
		Deletes the desired checklist (the directory).
		"""
		shutil.rmtree('/sdcard/operator/checklists/' + self.title)
		self.clear_widgets()
		self.do_get_checklists()

class FloatInput(TextInput):
	"""
	Text field that restricts input to numbers. Allows a negative sign and a period.
	"""
	input_type = 'number'

	def insert_text(self, substring, from_undo=False):
		if substring == "-":
			if self.cursor_col == 0 and "-" not in self.text:
				pass
			else:
				substring = ""
		else:
			chr = type(substring)
			if chr is bytes:
				int_pat = self._insert_int_patb
			else:
				int_pat = self._insert_int_patu
			if '.' in self.text:
				substring = re.sub(int_pat, chr(''), substring)
			else:
				substring = '.'.join([re.sub(int_pat, chr(''), k) for k in substring.split(chr('.'), 1)])
		return super(FloatInput, self).insert_text(substring, from_undo=False)