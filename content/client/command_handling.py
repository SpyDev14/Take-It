from aioconsole import ainput
from typing     import Dict, Set, List, Callable, Awaitable, Any
from asyncio    import Task, CancelledError
from pathlib    import Path
import asyncio, shlex, copy

from content.shared.dependencies import DependencyContainer, Ref
from content.shared.messages     import WebSocketInterface
from content.shared.models       import ClientModel, AddressModel
from content.shared.utils        import is_null_or_whitespace, print_notify, NotifyType
from content.client.shared       import print_send_file_command_info, incorrect_input


## Commands
async def send_command(
		command_args: List[str],
		suitable_clients: Dict[str, ClientModel],
		websocket: WebSocketInterface
	):
	if len(command_args) < 2:
		raise Exception('Необходимо указать <имя\\адрес клиента> и <путь до файла\\папки>')
	
	receiver: ClientModel | None = None
	path:     Path        | None = None
	
	try:
		receiver = suitable_clients.get(command_args[0])
		
		if not receiver:
			split_result: List[str] = command_args[0].split(':')
			
			address: AddressModel = AddressModel(
				host = split_result[0],
				port = int(split_result[1]),
			)
			
			# Вызовет исключение StopIteration, если ничего не найдёт
			receiver = next(
				client for client in suitable_clients.values()
				if client.address == address
			)
	except:
		raise Exception(f'Получатель указан неправильно')
	
	path = Path(command_args[1])
	if not path.exists():
		raise Exception('Путь указан неправильно')
	
	assert receiver and path
	
	
	files_for_sending: None  # Нужна модель
	await websocket.send('') # Отправка запроса на пересылку файла


async def help_command():
	print_send_file_command_info()


### Handler
class CommandHandler:
	"""
		#### Зависимости по умолчанию:
			`raw_user_input: str`     - ввод пользователя без изменений.
			`command_name: str`       - название команды.
			`command_args: List[str]` - аргументы в формате листа.

		:param command_handlers:   Обработчики команд, в формате вызываемых объектов с параметрами.
		:param dependencies:       Зависимости для обработчиков. Добавляемые по умолчанию объекты описаны выше.
		:param on_error_func:      Асинхронный вызываемый объект, вызываемый при необработанном исключении в коде обработчика.
		:param on_unknown_command: Синхронный вызываемый объект, вызываемый при попытке выполнить несуществующую команду.
		:param command_prefix:     Прификс командной строки. По умолчанию = `'>>> '`
	"""
	def __init__(
			self,
			command_handlers: Dict[str, Callable[..., Awaitable[None]]],
			*,
			dependencies:       DependencyContainer,
			on_unknown_command: Callable = incorrect_input,
			command_prefix:     str      = '>>> ',
			on_error_func:      Callable[[Exception], Awaitable[None]] | None = None
		):

		if not on_error_func:
			async def on_err(ex: Exception):
				print_notify(
					f"{f'{type(ex)}: ' if type(ex) != Exception else None}{ex}",
					NotifyType.ERRO
				)

			on_error_func = on_err

		self._command_handlers: Dict[str, Callable[..., Awaitable[None]]] = command_handlers

		self._dependencies:       DependencyContainer                    = dependencies
		self._command_prefix:     str                                    = command_prefix
		self._on_unknown_command: Callable                               = on_unknown_command
		self._on_error_func:      Callable[[Exception], Awaitable[None]] = on_error_func
	
	
	async def handler(self):
		raw_user_input: Ref[str | None] = Ref(None)
		command_name:   Ref[str | None] = Ref(None)
		command_args:  List[str]        = []


		dependencies: DependencyContainer = self._dependencies
		dependencies.add(
			raw_user_input = raw_user_input,
			command_name   = command_name,
			command_args   = command_args,
		)
		
		assert dependencies is self._dependencies
		assert dependencies.get('raw_user_input') is raw_user_input
		assert dependencies.get('command_name')   is command_name
		assert dependencies.get('command_args')   is command_args

		try:
			while True:
				raw_user_input.value = await ainput(self._command_prefix)
				if is_null_or_whitespace(raw_user_input.value):	continue
				
				prepared_input: List[str] = shlex.split(raw_user_input.value)
				command_name.value = prepared_input[0]
				del prepared_input[0]
				command_args = prepared_input


				if command_name.value not in self._command_handlers:
					self._on_unknown_command()
					continue

				command_func: Callable = self._command_handlers[command_name.value]
				
				try: await command_func(**dependencies.resolve(command_func))
				except Exception as ex:
					await self._on_error_func(ex)
				
		except CancelledError:
			pass

		except (EOFError, KeyboardInterrupt):
			pass