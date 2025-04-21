from websockets.exceptions     import ConnectionClosed, ConnectionClosedOK, ConnectionClosedError
from websockets                import connect, ClientConnection
from colorama                  import Fore, Style
from requests                  import Response
from asyncio                   import Task, TaskGroup, CancelledError
from typing                    import Dict, Callable, Awaitable
import asyncio, requests, colorama, copy

from content.client.command_handling import CommandHandler, help_command, send_command
from content.client.shared           import incorrect_input, is_client_suitable, print_client
from content.client.utils            import play_symbol_animation
from content.shared.dependencies     import DependencyContainer, Ref, resolve_and_call
from content.shared.info_enums       import WorkMode
from content.shared.messages         import MessageHandler, MessageType, MessageModel, WebSocketInterface
from content.shared.models           import ClientModel, ClientsModel
from content.shared.config           import INVALID_CHARACTERS
from content.shared.utils            import is_null_or_whitespace, print_notify, NotifyType
from content.shared.info             import Info, is_valid_name
import msg_handlers as handl


colorama.init(convert=True)
DEBUG: bool = True


##MARK: RECIEVER LOGIC
async def receiver_logic(websocket: WebSocketInterface):
	anim_task = asyncio.create_task(play_symbol_animation("Ожидание файла"))
	try:
		while True:
			data: str = await websocket.receive()

			msg_type = MessageModel.model_validate_json(data).type

			if msg_type.name == 'dd':
				print(data)
		# anim_task.cancel()
		# await anim_task
	except ConnectionClosed as e:
		raise e
	
	# except:
	# 	pass


##MARK: SENDER LOGIC
async def sender_logic(
		websocket: WebSocketInterface,
		server_ip: Ref[str],
		current_user_info: Info,
		this_dependency_container: DependencyContainer
	):

	COLUMN_WIDTH: int = 0
	suitable_clients: Dict[str, ClientModel] = {}
	
	dependencies = copy.copy(this_dependency_container)
	dependencies.add(
		suitable_clients = suitable_clients
	)

	
	print(f"\n{Style.BRIGHT}{"Доступные пользователи":^{COLUMN_WIDTH}}{Style.RESET_ALL}")
	
	## Ожидание получения клиентов
	async with TaskGroup() as tg:
		anim_task = tg.create_task(play_symbol_animation("Поиск..."))
		
		resp: Response = await asyncio.to_thread(requests.get, f"http://{server_ip.value}/clients/")
		clients:  Dict = ClientsModel.model_validate_json(resp.text).clients
		
		suitable_clients = {
			name: client 
			for name, client in clients.items()
			if is_client_suitable(client, current_user_info)
		}
		
		anim_task.cancel()
		del anim_task
	

	command_handler = CommandHandler(
		{
			'send' : send_command,
			'help' : help_command
		},
		dependencies = this_dependency_container
	)

	message_handler = MessageHandler(
		{
			MessageType.CLIENT_CONNECTED        : handl.on_client_connected,
			MessageType.CLIENT_DISCONNECTED     : handl.on_client_disconnected,
			MessageType.CLIENT_STATUS_CHANGED   : handl.on_client_status_changed
		},
		websocket,
		dependencies = this_dependency_container
	)

	# Отрисовка пользователей
	if len(suitable_clients) > 0:
		for client in suitable_clients.values():
			print_client(client)
	else:
		print_notify("Пользователей, подходящих для отправки сейчас нет", NotifyType.ERRO)

		# Тут мне нужно запустить анимацию ожидания до появления первого клиента.
		try:
			async with TaskGroup() as tg:
				# anim_task: Task = tg.create_task(play_symbol_animation("Ожидание клиентов..."))

				async def on_first_client_connected(this_dependency_container: DependencyContainer):
					await handl.on_client_connected(
						**this_dependency_container.resolve(handl.on_client_connected)
					)

					# anim_task.cancel()
					# произойдёт выход из контекстного менеджера
					# с завершением всех сопутствующих задач
					# (считай raise)

				temp_msg_handler = MessageHandler(
					{
						MessageType.CLIENT_CONNECTED : on_first_client_connected
					},
					message_handler.websocket,
					dependencies = message_handler.dependencies
				)

				tg.create_task(temp_msg_handler.handler())

		except* CancelledError: pass

	command_handling_task: Task = asyncio.create_task(command_handler.handler())
	message_handling_task: Task = asyncio.create_task(message_handler.handler())
		
	await asyncio.gather(
		command_handling_task,
		message_handling_task
	)


## MAIN
async def main():
	server_ip: str      | None = None
	work_mode: WorkMode | None = None
	user_name: str      | None = None

	client_logics: Dict[WorkMode, Callable[..., Awaitable[None]]] = {
		WorkMode.RECEIVER : receiver_logic,
		WorkMode.SENDER   : sender_logic
	}

	##MARK: IF DEBUG
	if DEBUG:
		from random import randint

		server_ip: Ref[str] = Ref('127.0.0.1:8000')
		user_name = str(randint(-16384, 16384))
		work_mode = WorkMode.SENDER


	##MARK: START
	try:
		print(f"\nДобро пожаловать в {Fore.CYAN}Take It{Fore.RESET}!\n")

		while not user_name:
			answer = input("Укажите своё имя: ")

			if is_null_or_whitespace(answer):
				incorrect_input()
				continue

			if not is_valid_name(answer):
				clr: str = Fore.YELLOW # Color
				res: str = Fore.RESET  # Reset
				incorrect_input(f"имя содержит недопустимые символы ({clr}{f'{res}, {clr}'.join(INVALID_CHARACTERS)}{res})")
				continue


			user_name = answer


		print(f"""
Выберите режим работы
{Fore.CYAN}0{Fore.RESET} - {Fore.CYAN}R{Fore.RESET}ECEIVE
{Fore.CYAN}1{Fore.RESET} - {Fore.CYAN}S{Fore.RESET}END
		""".strip())
		
		while not work_mode:
			answer = input(f">>> ").strip().lower()

			if answer in {'0', 'receive', 'r'}:
				work_mode = WorkMode.RECEIVER
				break

			elif answer in {'1', 'send', 's'}:
				work_mode = WorkMode.SENDER
				break

			incorrect_input()

		current_user_info = Info(user_name, work_mode)
		del user_name, work_mode

		print(f"""
name: {Fore.CYAN}{current_user_info.user_name     }{Fore.RESET}	
mode: {Fore.CYAN}{current_user_info.work_mode.name}{Fore.RESET}
		""")


		anim_task = asyncio.create_task(play_symbol_animation("Подключение к серверу..."))
		async with connect(f"ws://{server_ip.value}/ws/") as ws:
			anim_task.cancel()
			await anim_task
			
			print_notify("Установлено соединение с сервером")
			await ws.send(f"{current_user_info.to_model().model_dump_json()}")

			dependencies = DependencyContainer(
				websocket = WebSocketInterface(
					receive = ws.recv,
					send    = ws.send
				),

				current_user_info = current_user_info,
				server_ip         = server_ip,
			)

			logic: Callable[..., Awaitable] = client_logics[current_user_info.work_mode]
			await logic(**dependencies.resolve(logic))


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
	except (ConnectionClosed, ConnectionClosedError) as e:
		print_notify(f"Соединение разорванно с кодом {e.code}{(f", причина: '{e.reason}'" if e.reason else "")}", NotifyType.FATL)

	# ошибка закрытия приложения через ctrl+c
	except KeyboardInterrupt:
		import sys
		sys.exit()

asyncio.run(main())