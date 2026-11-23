from colorama import Fore
from typing   import List

from content.shared.info_enums import WorkMode, ClientState
from content.shared.models     import ClientModel
from content.shared.info       import Info
from content.shared.utils      import print_notify, NotifyType

def incorrect_input(desc: str | None = None):
	print_notify(f"Неправильный ввод{f": {desc}." if desc else '!'}", NotifyType.ERRO)

def print_send_file_command_info():
	def cyan(text: str) -> str:
		return f"{Fore.CYAN}{text}{Fore.RESET}"
	
	print_notify(f"Чтобы отправить: {cyan('send')} <{cyan('receiver: name | address')}> <{cyan('path: file | dirr')}>")

def is_client_suitable(client: ClientModel, current_user_info: Info) -> bool:
	return (
		client.info.user_name != current_user_info.user_name and
		client.info.work_mode == WorkMode.RECEIVER           and
		client.state          == ClientState.AWAIT
	)

def print_client(client: ClientModel, *, label: str | None = None):
	first_line_shell:  str = " ╓ {} ╖"
	middle_line_shell: str = " ║ {} ║"
	last_line_shell:   str = " ╙ {} ╜"

	# просто чтобы чуть ниже было всё красиво и легкочитаемо
	name: str = client.info.user_name
	adress: str = f"{client.address.host}:{client.address.port}"
	state: str = client.state.name

	msg_lines: List[str] = [
		f"Client: {Fore.YELLOW}{name}{Fore.RESET}",
		f"Adress: {Fore.CYAN}{adress}{Fore.RESET}",
		f"Status: {Fore.GREEN}{state}{Fore.RESET}"
	]
	max_line_len: int = max(map(len, msg_lines))

	for i in range(len(msg_lines)):
		if len(msg_lines[i]) >= max_line_len:
			continue
		msg_lines[i] += ' '*(max_line_len - len(msg_lines[i]))

	# last_index
	last_i: int = len(msg_lines) - 1

	msg_lines[0]      =  first_line_shell.format(msg_lines[0])
	for i in range(1, len(msg_lines) - 1):
		msg_lines[i]  = middle_line_shell.format(msg_lines[i])
	msg_lines[last_i] =   last_line_shell.format(msg_lines[last_i])
		
	if label:
		print(label)
	print(f"{'\n'.join(msg_lines)}\n")