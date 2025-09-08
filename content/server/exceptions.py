class ClientSideError(Exception):
	"""Общее исключение для ошибок со стороны клиента"""
	def __init__(self, description: str | None = None, *args):
		super().__init__(*args)

		self.description: str | None = description