from pydantic import BaseModel, Field, ValidationError
from asyncio  import Task, CancelledError
from typing   import Dict, Callable, Awaitable, Literal
from enum     import Enum
import asyncio

from content.shared.dependencies import DependencyContainer, Ref
from content.shared.info_enums   import ClientState
from content.shared.models       import ClientModel
from content.shared.utils        import print_notify, NotifyType



class WebSocketInterface:
	def __init__(
			self,
			*,
			receive: Callable[[],     Awaitable[bytes | str]],
			send:    Callable[[bytes | str], Awaitable[None]] 
		):

		self._receive: Callable[[],     Awaitable[bytes | str]] = receive
		self._send:    Callable[[bytes | str], Awaitable[None]] = send

	# публичные методы для удобного и понятного взаимодействия
	async def receive(self) -> bytes | str:
		return await self._receive()
	
	async def send(self, data: bytes | str) -> None:
		await self._send(data)

class MessageType(Enum):
	CLIENT_CONNECTED      = 'client_connected'
	CLIENT_DISCONNECTED   = 'client_disconnected'
	CLIENT_STATUS_CHANGED = 'client_status_changed'

	FILE_FORWARDING_REQUEST = 'file_forwarding_request' # Client -> Server
	FILE_FORWARDING_ACCEPT  = 'file_forwarding_accept'  # Server -> Client

class MessageModel(BaseModel):
	type: MessageType = Field(frozen=True)

class MessageHandler:
	"""
	#### Зависимости по умолчанию:
		`websocket: WebSocketInterface` - вебсокет. 
		`received_data: str | bytes` - полученная по websocket строка текста либо очередь байтов.

	:param message_handlers: Обработчики вебсокет сообщений, в формате вызываемых объектов с параметрами.

	:param websocket: WebSocketInterface для работы этого обработчика.
		Также передаётся в контейнер зависимостей.

	:param dependencies: Зависимости для обработчиков. Добавляемые по умолчанию объекты описаны выше.

	:param on_error_func: Асинхронный вызываемый объект, вызываемый при необработанном исключении
		в коде обработчика.	Если ничего не указанно - используется своя асинхронная функция,
		на основе `print_notify` с режимом `ERRO`.

	:param timeout: Максимальное время выполнения обработки сообщения. Если необходимо отключить - укажите 0.
	"""
	
	def __init__(
			self,
			message_handlers: Dict[MessageType, Callable[..., Awaitable]],
			websocket:        WebSocketInterface,
			*,
			dependencies:  DependencyContainer = DependencyContainer(),
			timeout:       float                                  | None = 15,
			on_error_func: Callable[[Exception], Awaitable[None]] | None = None
		):

		if websocket not in dependencies:
			dependencies.add(websocket = websocket)
		assert dependencies.get('websocket') is websocket

		if not on_error_func:
			async def on_err(ex: Exception):
				print_notify(
					f"{f'{type(ex)}: ' if type(ex) != Exception else None}{ex}",
					NotifyType.ERRO
				)

			on_error_func = on_err
		
		self._message_handlers: Dict[MessageType, Callable[..., Awaitable]] = message_handlers
		self._websocket:        WebSocketInterface                          = websocket
		
		self._dependencies:     DependencyContainer                         = dependencies
		self._on_error_func:    Callable[[Exception], Awaitable]            = on_error_func
		self._timeout:          float | None                                = timeout


	async def handler(self):
		message_type:  MessageType
		received_data: Ref[str | bytes | None] = Ref(None)

		message_handling: Task | None = None
		error_handling:   Task | None = None

		dependencies: DependencyContainer = self._dependencies
		dependencies.add(received_data = received_data)

		assert dependencies.get('received_data') is received_data

		ws: WebSocketInterface = self._websocket

		def on_error(error: Exception):
			"""Нужно вызывать при ошибке, если её нужно как-то обработать"""
			nonlocal error_handling

			message_handling.cancel()

			if self._on_error_func:
				error_handling = asyncio.create_task(self._on_error_func(error))


		async with asyncio.timeout(self._timeout):
			try:
				while True:
					received_data.value = await ws.receive()

					try:    message_type = MessageModel.model_validate_json(received_data.value).type
					except ValidationError:
						continue

					if message_type not in self._message_handlers: continue


					handle_function: Callable = self._message_handlers[message_type]
					message_handling: Task = asyncio.create_task(handle_function(**dependencies.resolve(handle_function)))


					try: await message_handling
					except TimeoutError: continue
					except Exception as ex:
						on_error(ex)
						await error_handling


			except CancelledError:
				if not message_handling:
					return
				
				elif not message_handling.cancelled():
					try:
						await message_handling

					except TimeoutError:
						return
					except Exception as ex:
						on_error(ex)
				
				if error_handling:
					await error_handling
	
	@property
	def websocket(self) -> WebSocketInterface:
		return self._websocket
	
	@property
	def dependencies(self) -> DependencyContainer:
		return self._dependencies



## MARK: Directly messages

class ClientDisconnectedMessage(MessageModel):
	type: Literal[MessageType.CLIENT_DISCONNECTED] = Field(default=MessageType.CLIENT_DISCONNECTED, frozen=True)

	disconnected_client: ClientModel

class ClientConnectedMessage(MessageModel):
	type: Literal[MessageType.CLIENT_CONNECTED] = Field(default=MessageType.CLIENT_CONNECTED, frozen=True)

	connected_client: ClientModel

class ClientStatusChangedMessage(MessageModel):
	type: Literal[MessageType.CLIENT_STATUS_CHANGED] = Field(default=MessageType.CLIENT_STATUS_CHANGED, frozen=True)

	client:    ClientModel
	new_state: ClientState
	old_state: ClientState

"""
class FileSendingStartMessage(MessageModel):
	type: Literal[MessageType.FILE_FORWARDING_REQUEST] = Field(default=MessageType.FILE_FORWARDING_REQUEST, frozen=True)

	receiver: ClientModel
	sender:   ClientModel

	file_info: FileInfoModel

class FileSendingAcceptMessage(MessageModel):
	type: Literal[MessageType.FILE_FORWARDING_ACCEPT] = Field(default=MessageType.FILE_FORWARDING_ACCEPT, frozen=True)

	chunk_size: int
"""