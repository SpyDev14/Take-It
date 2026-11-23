from colorama import Fore
from typing   import Any
from enum     import Enum

def is_null_or_whitespace(s: str | None) -> bool:
	"""
	Проверяет, является ли строка `None`, пустой или состоит только из whitespace символов.
	
	:param s: Проверяемая строка
	:return: True если строка None, пустая или содержит только пробельные символы
	"""
	
	return s is None or (not s.strip())

class NotifyType(Enum):
	INFO: str = Fore.CYAN
	DEBG: str = Fore.BLUE
	WARN: str = Fore.YELLOW
	ERRO: str = Fore.RED
	FATL: str = Fore.MAGENTA

		
def print_notify(
		message: str | Any,
		notify_type: NotifyType = NotifyType.INFO,
		*,
		notify_shell: str = '[{0}]',
		start_with = '\r',
		ends_with='\n'
	) -> str:

	msg = f"{start_with}{notify_shell.format(f'{notify_type.value}{notify_type.name}{Fore.RESET}')} {message}"

	print(msg, end=ends_with)
	return msg