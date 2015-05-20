# -*- coding: utf-8 -*-
#
# SecureState Operator
# https://github.com/securestate/operator
#
# THIS IS PROPRIETARY SOFTWARE AND IS NOT TO BE PUBLICLY DISTRIBUTED

import time

from jnius import autoclass

MediaRecorder = autoclass('android.media.MediaRecorder')
AudioSource = autoclass('android.media.MediaRecorder$AudioSource')
OutputFormat = autoclass('android.media.MediaRecorder$OutputFormat')
AudioEncoder = autoclass('android.media.MediaRecorder$AudioEncoder')
File = autoclass('java.io.File')

class SoundRecorder(object):
	"""Class to manage the recorder object"""
	def __init__(self):
		self.recorder = MediaRecorder()
		self.storage_path = '/storage/sdcard0/' + time.strftime('%Y-%m-%d-%H-%M-%S') + '.3gp'
		self.is_recording = False

	def init_recorder(self):
		"""Initialize the recorder."""
		self.recorder.setAudioSource(AudioSource.MIC)
		self.recorder.setOutputFormat(OutputFormat.THREE_GPP)
		self.recorder.setAudioEncoder(AudioEncoder.AMR_NB)
		self.recorder.setOutputFile(self.storage_path)
		self.recorder.prepare()

	def start(self):
		"""Start the recorder."""
		if self.is_recording:
			self.recorder.stop()
			self.recorder.reset()
			self.is_recording = False
			return

		self.init_recorder()
		self.recorder.start()
		self.is_recording = True

	def stop(self):
		"""Stop the recorder."""
		if not self.is_recording:
			return
		self.recorder.stop()
		self.recorder.reset()
		self.is_recording = False
