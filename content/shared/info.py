from typing import Self

from content.shared.config     import INVALID_CHARACTERS
from content.shared.info_enums import WorkMode
from content.shared.models     import InfoModel

def is_valid_name(name: str) -> bool:
	return not any(char in INVALID_CHARACTERS for char in name)

class Info:
	def __init__(self, user_name: str, work_mode: WorkMode):
		self.user_name: str = user_name
		self.work_mode: WorkMode = work_mode

	@classmethod
	def from_model(cls, model: InfoModel) -> Self:
		return cls(model.user_name, model.work_mode)

	def to_model(self) -> InfoModel:
		return InfoModel(
			user_name = self.user_name,
			work_mode = self.work_mode
		)