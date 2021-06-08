import json

class checkpoint_parser:
	_CHECKPOINT_TAG = "checkpoints"
	_THREAD_START_ROUTINE_TAG = "thread_start_routines"

	def __init__(self, checkpoint_file_name):
		with open(checkpoint_file_name) as checkpoint_file:
			self._information = json.load(checkpoint_file)

	def get_start_routines(self):
		return self._information[self._THREAD_START_ROUTINE_TAG]

	def get_checkpoints(self):
		return self._information[self._CHECKPOINT_TAG]
