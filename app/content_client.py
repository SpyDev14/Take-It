from websockets            import connect, ClientConnection, Data
from websockets.exceptions import ConnectionClosed, ConnectionClosedOK
from requests              import Response
from typing                import Dict, Callable, Tuple, List
from colorama              import Fore, Style
from aioconsole            import ainput
import asyncio, requests, time, colorama

from shared                import WorkMode, Info, ClientState 
from shared                import ClientsModel, ClientModel
from shared                import MessageType, MessageModel, ClientConnectedMessageModel, ClientDisconnectedMessageModel
from shared                import INVALID_CHARACTERS, is_valid_name
from utils                 import is_null_or_whitespace, print_notify, NotifyType, play_simboll_animation, PreparedAnimations

## Функции
def incorrect_input():
	print_notify("Неправильный ввод!", NotifyType.ERRO)

##MARK: START
server_ip: str = '127.0.0.1:8000'
work_mode: WorkMode | None = None
user_name: str      | None = None
DEBUG: bool = True

colorama.init()

##MARK: IF DEBUG
# user_name = "Николае Чаушеско"
# work_mode = WorkMode.SENDER


print(f"\nДобро пожаловать в {Fore.CYAN}Take It{Fore.RESET}!\n")

while user_name == None:
	answer = input("Укажите своё имя: ")

	if is_null_or_whitespace(answer):
		incorrect_input()
		continue

	user_name = answer

print(f"""
Выберите режим работы
 {Fore.CYAN}0{Fore.RESET} - {Fore.CYAN}R{Fore.RESET}ECEIVE
 {Fore.CYAN}1{Fore.RESET} - {Fore.CYAN}S{Fore.RESET}END
 """.strip())
while work_mode == None:
	answer = input(f">>> ").strip().lower()

	if answer in ("0", "receive", 'r'):
		work_mode = WorkMode.RECEIVER
		break

	elif answer in ("1", "send", 's'):
		work_mode = WorkMode.SENDER
		break

	incorrect_input()

info = Info(user_name, work_mode)
del user_name, work_mode

print(f"""
name: {Fore.CYAN}{info.user_name}{Fore.RESET}	
mode: {Fore.CYAN}{info.work_mode.name}{Fore.RESET}
""")




##MARK: RECIEVER LOGIC
async def receiver_logic(ws: ClientConnection):
	anim_task = asyncio.create_task(play_simboll_animation("Ожидание файла"))
	try:
		while True:
			data: str = await ws.recv()

			msg_type = MessageModel.model_validate_json(data).type

			if (msg_type.name == 'dd'):
				print(data)
		# anim_task.cancel()
		# await anim_task
	except ConnectionClosed as e:
		raise e
	
	except:
		pass



##MARK: SENDER LOGIC
suitable_clients: Dict[str, ClientModel] = {}

def print_send_file_command_info():
	print_notify(f"Чтобы отправить: {Fore.CYAN}send{Fore.RESET} <{Fore.CYAN}receiver: name | address{Fore.RESET}> <{Fore.CYAN}path: file | dirr{Fore.RESET}>")

def is_client_suitable(client: ClientModel) -> bool:
	return (
		client.info.work_mode == WorkMode.RECEIVER and
		client.info.user_name != info.user_name    and
		client.state          == ClientState.AWAIT
	)

def print_client(client: ClientModel, *, label: str | None = None):
	first_line_shell:  str = " ╓ {} ╖"
	middle_line_shell: str = " ║ {} ║"
	last_line_shell:   str = " ╙ {} ╜"

	# просто чтобы чуть ниже было всё красиво и легкочитаемо
	name: str = client.info.user_name
	adress: str = f"{client.adress.host}:{client.adress.port}"
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



##MARK: WS MESSAGES HANDLING
async def on_client_connected(msg: str):
	client: ClientModel = ClientConnectedMessageModel.model_validate_json(msg).connected_client
					
	if not is_client_suitable(client):
		return
	
	# MARK: возможно будут баги
	suitable_clients[client.info.user_name] = client
	print_client(client, label=f'{Fore.GREEN}\nНовый пользователь{Fore.RESET}')

async def on_client_disconnected(msg: str):
	client: ClientModel = ClientDisconnectedMessageModel.model_validate_json(msg).disconnected_client

	# MARK: возможно будут баги
	if client in suitable_clients.values():
		del suitable_clients[client.info.user_name]

		print_notify(f"Пользователь \"{Fore.CYAN}{client.info.user_name}{Fore.RESET}\" отключился", NotifyType.WARN)

async def ws_message_handler(ws: ClientConnection):
	MESSAGE_HANDLERS: Dict[MessageType, Callable[[str], None]] = {
		MessageType.CLIENT_CONNECTED    : on_client_connected,
		MessageType.CLIENT_DISCONNECTED : on_client_disconnected
	}

	msg: str
	type: MessageType
	task = None

	try:
		while True:
			msg  = await ws.recv()
			type = MessageModel.model_validate_json(msg).type

			task = asyncio.create_task(MESSAGE_HANDLERS[type](msg))
			await task

	except asyncio.CancelledError:
		if task:
			await task

## END: WS MESSAGES HANDLING



##MARK: COMMAND HANDLER
### START: COMMANDS

async def send_command(raw_input: str, ws: ClientConnection) -> bool:
	args: List[str] = raw_input.split(' ')

	receiver: str | None = None
	path:     str | None = None

	del args[0]

	if len(args) < 2:
		print_notify("Необходимо указать имя\\адрес клиента, а также путь до файла\\папки", NotifyType.ERRO)
		return False
	
	if len(args >= 2):
		receiver = args[0]
		path = args[1]

	if len(args > 2):
		pass

	print_notify("Method send_file() not implemented", NotifyType.DEBG)
	return False

async def help_command(args: str, ws: ClientConnection) -> bool:
	print_send_file_command_info()
	return True

### END: COMMANDS

async def command_handler(ws: ClientConnection):
	COMMANDS: Dict[str, Callable[[str, ClientConnection], bool]] = {
		"send" : send_command,
		"help" : help_command
	}

	raw_input:    str | None = None
	command_name: str | None = None
	task = None

	try:
		while True:
			raw_input = await ainput(">>> ")

			if is_null_or_whitespace(raw_input):
				continue
			
			command_name = raw_input.split(' ')[0]

			if command_name not in COMMANDS:
				incorrect_input()
				continue

			task = asyncio.create_task(COMMANDS[command_name](raw_input, ws))
			await task
			
	except asyncio.CancelledError:
		if task:
			await task
	except EOFError:
		pass
## END: COMMAND HANDLER



async def sender_logic(ws: ClientConnection):
	COLUMN_WIDTH:  int   = 0
	
	print(f"\n{Style.BRIGHT}{"Доступные пользователи":^{COLUMN_WIDTH}}{Style.RESET_ALL}")
	
	async with asyncio.TaskGroup() as tg:
		anim_task = tg.create_task(play_simboll_animation("Поиск..."))
		
		resp: Response = await asyncio.to_thread(requests.get, f"http://{server_ip}/clients/")
		clients = ClientsModel.model_validate_json(resp.text).clients
		
		suitable_clients = {name: client for name, client in clients.items() if is_client_suitable(client)}
		
		anim_task.cancel()
	
	# Отрисовка пользователей
	if len(suitable_clients) > 0:
		for client in suitable_clients.values():
			print_client(client)
	else:
		print_notify("Пользователей, подходящих для отправки сейчас нет", NotifyType.ERRO)
	
	print_send_file_command_info()

	ws_messahe_handling = asyncio.create_task(ws_message_handler(ws))
	command_handling    = asyncio.create_task(command_handler(ws))
	
	await ws_messahe_handling
	await command_handling


client_logics: Dict[WorkMode, Callable[[ClientConnection], None]] = {
	WorkMode.RECEIVER : receiver_logic,
	WorkMode.SENDER   :   sender_logic
}

##MARK: MAIN
async def main():
	anim_task = asyncio.create_task(play_simboll_animation("Подключение к серверу..."))
	try:
		async with connect(f"ws://{server_ip}/ws/") as ws:
			anim_task.cancel()
			await anim_task
			
			print_notify("Установлено соединение с сервером")
			await ws.send(f"{info.to_model().model_dump_json()}")
			
			await client_logics[info.work_mode](ws)

	# ошибки, которые могут возникнуть до подключения
	except (TimeoutError, ConnectionRefusedError) as e:
		anim_task.cancel()
		await anim_task
		
		if isinstance(e, TimeoutError):
			print_notify("Превышено время ожидания ответа от сервера", NotifyType.FATL)
		else:
			print_notify("Сервер не доступен", NotifyType.FATL)
		
	# ошибки, которые могут возникнуть после подключения
	except ConnectionClosedOK as e:
		print_notify(f"Соединение закрыто успешно с кодом {e.code}")
	except ConnectionClosed as e:
		print_notify(f"Соединение разорванно с кодом {e.code}{(f", причина: '{e.reason}'" if e.reason else "")}", NotifyType.FATL)

asyncio.run(main())