from aioconsole import ainput
from typing     import Dict, Set, List, Callable, Awaitable, Any
from asyncio    import Task, CancelledError
import asyncio, shlex, copy

from content.shared.dependencies import DependencyContainer, Ref
from content.shared.utils        import is_null_or_whitespace, print_notify, NotifyType
from content.client.shared       import print_send_file_command_info, incorrect_input


## Commands
async def send_command(command_args:  List[str]):
	if len(command_args) < 2:
		raise Exception('Необходимо указать <имя\\адрес клиента>, а также путь до <файла\\папки>')
	
	receiver = command_args[0]
	path     = command_args[1]
	
	
	# На будущее
	if False:
		raise Exception('Аргументы указанны неправильно')

	print_notify("Send command not implemented :(", NotifyType.DEBG)


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
			dependencies:      DependencyContainer,
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

		self._dependencies:      DependencyContainer                    = dependencies
		self._on_error_func:     Callable[[Exception], Awaitable[None]] = on_error_func
		self._on_unknow_command: Callable                               = on_unknow_command
		self._command_prefix:    str                                    = command_prefix
	
	
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
					self._on_unknow_command()
					continue

				command_func: Callable = self._command_handlers[command_name.value]
				
				try: await command_func(**dependencies.resolve(command_func))
				except Exception as ex:
					await self._on_error_func(ex)
				
		except CancelledError:
			pass

		except (EOFError, KeyboardInterrupt):
			pass