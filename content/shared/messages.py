from pydantic import BaseModel, Field
from asyncio  import Task, CancelledError
from typing   import Dict, Callable, Awaitable, Any, Literal, Union
from enum     import Enum
import asyncio

from content.shared.dependencies import DepencyContainer, Ref
from content.shared.info_enums   import ClientState
from content.shared.models       import ClientModel, FileInfoModel
from content.client.utils        import print_notify, NotifyType # Говно решение???



class WebSocketInterface():
	def __init__(
			self,
			*,
			receive: Callable[[],     Awaitable[bytes | str]],
			send:    Callable[[bytes | str], Awaitable[None]] 
		):

		self._receive: Callable[[],     Awaitable[bytes | str]] = receive
		self._send:    Callable[[bytes | str], Awaitable[None]] = send

	async def receive(self) -> bytes | str:
		return await self._receive()
	
	async def send(self, data: bytes | str) -> None:
		await self._send(data)

class MessageType(Enum):
	CLIENT_CONNECTED      = 'client.connected'
	CLIENT_DISCONNECTED   = 'client.disconnected'
	CLIENT_STATUS_CHANGED = 'client.status_changed'

	FILE_FORWARDING_REQUEST = 'file_forwarding.request'
	FILE_FORWARDING_ACCEPT  = 'file_forwarding.accept'

class MessageModel(BaseModel):
	type: MessageType = Field(frozen=True)

class MessageHandler():
	"""
	#### Зависимости по умолчанию:
		`websocket: WebSocketInterface` - вебсокет. 
		`received_data: bytes` - полученная по websocket строка текста.

	:param message_handlers: Обработчики вебсокет сообщений, в формате вызываемых объектов с параметрами.
	:param websocket:        WebSocketInterface для работы этого обработчика. также передаётся в контейнер зависимостей.
	:param dependencies:     Зависимости для обработчиков. Добавляемые по умолчанию объекты описаны выше.
	:param on_error_func:    Асинхронный вызываемый объект, вызываемый при необработанном исключении в коде обработчика.
	:param timeout:          Максимальное время выполнения обработки сообщения. Если необходимо отключить - укажите 0.
	"""
	
	def __init__(
			self,
			message_handlers: Dict[MessageType, Callable[[str], None]],
			websocket:        WebSocketInterface,
			*,
			dependencies:  DepencyContainer | None = None,
			timeout:       float            | None = 15,
			on_error_func: Callable[[Exception], Awaitable[None]] | None = None
		):

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
		
		self._dependencies:     DepencyContainer                            = dependencies
		self._on_error_func:    Callable[[Exception], Awaitable]            = on_error_func
		self._timeout:          float | None                                = timeout


	async def handler(self):
		message_type:  MessageType
		received_data: Ref[str | bytes | None] = Ref(None)

		message_handling: Task | None = None
		error_handling:   Task | None = None

		dependencies: DepencyContainer = self._dependencies
		dependencies.add(received_data = received_data)

		assert dependencies.get('received_data') is received_data

		ws: WebSocketInterface = self._websocket

		def on_error(ex: Exception):
			'''Нужно вызывать при ошибке, если её нужно как-то обработать'''
			nonlocal error_handling

			message_handling.cancel()

			if self._on_error_func:
				error_handling = asyncio.create_task(self._on_error_func(ex))


		async with asyncio.timeout(self._timeout):
			try:
				while True:
					received_data = await ws.receive()

					try:    message_type = MessageModel.model_validate_json(received_data).type
					except:	continue

					if message_type not in self._message_handlers: continue


					handl_function: Callable = self._message_handlers[message_type]
					message_handling: Task = asyncio.create_task(handl_function(**dependencies.resolve(handl_function)))	


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
	def dependencies(self) -> DepencyContainer:
		return self._dependencies



## MARK: Dirrectly messages

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

class FileSendingStartMessage(MessageModel):
	type: Literal[MessageType.FILE_FORWARDING_REQUEST] = Field(default=MessageType.FILE_FORWARDING_REQUEST, frozen=True)

	receiver: ClientModel
	sender:   ClientModel

	file_info: FileInfoModel

class FileSendingAcceptMessage(MessageModel):
	type: Literal[MessageType.FILE_FORWARDING_ACCEPT] = Field(default=MessageType.FILE_FORWARDING_ACCEPT, frozen=True)

	chunk_size: int