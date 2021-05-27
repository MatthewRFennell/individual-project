class checkpoint_parser:
	_ENTRY_POINT_TAG_NAME = "entry_points"
	_CHECKPOINT_TAG_NAME = "checkpoints"

	def __init__(self, checkpoint_file_name):
		with open(checkpoint_file_name) as checkpoint_file:
			self._information = json.load(checkpoint_file)

	def get_entry_points(self):
		return self._information[self._ENTRY_POINT_TAG_NAME]

	def get_checkpoints(self):
		return self._information[self._CHECKPOINT_TAG_NAME]
