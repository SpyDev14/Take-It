def is_null_or_whitespace(s: str) -> bool:
	"""
	:param s: Произвольная строка
	:return: Bool значение, говорящее пустая строка, или нет.
	"""
	return s is None or len(s.strip()) == 0

