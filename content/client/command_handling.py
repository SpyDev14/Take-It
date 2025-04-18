from aioconsole import ainput
from typing     import Dict, Set, List, Callable, Awaitable, Any
from asyncio    import Task, CancelledError
import asyncio, shlex

from content.shared.dependencies import DepencyContainer, Ref
from content.shared.utils        import is_null_or_whitespace
from content.client.shared       import print_send_file_command_info, incorrect_input
from content.client.utils        import print_notify, NotifyType 


## Commands
async def send_command(command_args:  List[str]):
	args: List[str] = command_args
	
	if len(args) < 2:
		raise Exception('Необходимо указать <имя\\адрес клиента>, а также путь до <файла\\папки>')
	
	receiver = args[0]
	path     = args[1]
	
	
	if not receiver or not path:
		raise Exception('Аргументы указанны неправильно')
	
	print_notify("Method send_file() not implemented", NotifyType.DEBG)
	raise NotImplementedError()


async def help_command():
	print_send_file_command_info()


### Handler
class CommandHandler:
	"""
		#### Зависимости по умолчанию:
			`raw_user_input: str`     - ввод пользователя без изменений.
			`command_name: str`       - название команды.
			`command_args: List[str]` - аргументы в формате листа.

		:param command_handlers:  Обработчики команд, в формате вызываемых объектов с параметрами.
		:param dependencies:      Зависимости для обработчиков. Добавляемые по умолчанию объекты описаны выше.
		:param on_error_func:     Асинхронный вызываемый объект, вызываемый при необработанном исключении в коде обработчика.
		:param on_unknow_command: Синхронный вызываемый объект, вызываемый при попытке выполнить несуществующую команду.
		:param command_prefix:    Прификс командной строки. По умолчанию = `'>>> '`
	"""
	def __init__(
			self,
			command_handlers: Dict[str, Callable[..., Awaitable[None]]],
			*,
			dependencies:      DepencyContainer,
			on_unknow_command: Callable = incorrect_input,
			command_prefix:    str      = '>>> ',
			on_error_func:     Callable[[Exception], Awaitable[None]] | None = None
		):

		if not on_error_func:
			async def on_err(ex: Exception):
				print_notify(
					f"{f'{type(ex)}: ' if type(ex) != Exception else None}{ex}",
					NotifyType.ERRO
				)

			on_error_func = on_err

		self._command_handlers: Dict[str, Callable[..., Awaitable[None]]] = command_handlers

		self._dependencies:      DepencyContainer                       = dependencies
		self._on_error_func:     Callable[[Exception], Awaitable[None]] = on_error_func
		self._on_unknow_command: Callable                               = on_unknow_command
		self._command_prefix:    str                                    = command_prefix
	
	
	async def handler(self):
		raw_user_input: Ref[str | None] = Ref(None)
		command_name:   Ref[str | None] = Ref(None)
		command_args:  List[str]        = []

		command_handling: Task | None = None
		error_handling:   Task | None = None

		dependencies: DepencyContainer = self._dependencies
		dependencies.add(
			raw_user_input = raw_user_input,
			command_name   = command_name,
			command_args   = command_args
		)

		assert dependencies is self._dependencies
		assert dependencies.get('raw_user_input') is raw_user_input
		assert dependencies.get('command_name')   is command_name
		assert dependencies.get('command_args')   is command_args

		def on_error(ex: Exception):
			'''Нужно вызывать при ошибке, если её нужно как-то обработать'''
			nonlocal error_handling

			command_handling.cancel()

			if self._on_error_func:
				error_handling = asyncio.create_task(self._on_error_func(ex))
	
		try:
			while True:
				raw_user_input.value = await ainput(self._command_prefix)
				if is_null_or_whitespace(raw_user_input.value):	continue
				
				prepared_input: List[str] = shlex.split(raw_user_input.value)
				command_name.value = prepared_input[0]
				del prepared_input[0]
				command_args = prepared_input


				if command_name not in self._command_handlers:
					self._on_unknow_command()
					continue

				command_func: Callable = self._command_handlers[command_name]
				command_handling = asyncio.create_task(command_func(**dependencies.resolve(command_func)))
				
				try: await command_handling
				except Exception as ex:
					on_error(ex)

					await error_handling
				
		except CancelledError:
			if not command_handling:
				return
			
			elif not command_handling.cancelled():
				try:
					await command_handling
				except Exception as ex:
					on_error(ex)

			if error_handling:
				await error_handling

		except (EOFError, KeyboardInterrupt):
			pass