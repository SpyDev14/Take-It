from starlette.types import Message
from pydantic        import BaseModel, Field
from asyncio         import Task, CancelledError
from typing          import Dict, Callable, Awaitable, Any, Literal
from enum            import Enum
import asyncio

from content.shared.info_enums import ClientState
from content.shared.models     import ClientModel, FileInfoModel
from content.client.utils      import print_notify, NotifyType # Говно решение???

class WebSocketInterface():
	def __init__(
			self, *,
			receive: Callable[[],        Awaitable[Any] ],
			send:    Callable[[Message], Awaitable[None]] 
		):

		self._receive: Callable[[],        Awaitable[Any] ] = receive
		self._send:    Callable[[Message], Awaitable[None]] = send

	async def receive(self) -> Any:
		return await self._receive()
	
	async def send(self, data: Message) -> None:
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
	def __init__(
			self,
			message_handlers: Dict[MessageType, Callable[[str], None]],
			ws: WebSocketInterface,
			*,
			on_error: Callable[[Exception], Awaitable[Any]] = lambda ex: print_notify(ex, NotifyType.ERRO),
			timeout: float | None = 15
		):

		self._MESSAGE_HANDLERS: Dict[MessageType, Callable[[str], None]] = message_handlers
		self._ws:               WebSocketInterface                       = ws
		self._on_error:         Callable[[Exception], Awaitable[Any]]    = on_error
		self._timeout:          float | None                             = timeout

	async def handler(self, *args, **kwargs):
		type: MessageType
		raw_msg: str

		task:           Task | None = None
		error_handlyng: Task | None = None

		def on_error_tasks_preparing(ex: Exception):
			nonlocal error_handlyng

			task.cancel()
			error_handlyng = asyncio.create_task(self._on_error(ex))
		
		async with asyncio.timeout(self._timeout):
			try:
				while True:
					raw_msg = await self._ws.receive()

					try:    type = MessageModel.model_validate_json(raw_msg).type
					except:	continue

					if type not in self._MESSAGE_HANDLERS:
						continue

					task: Task = asyncio.create_task(self._MESSAGE_HANDLERS[type](raw_msg, *args, **kwargs))

					try: await task

					except TimeoutError:
						continue
					except Exception as ex:
						on_error_tasks_preparing(ex)
						await error_handlyng

			except CancelledError:
				if not task:
					return
				
				if not task.cancelled():
					try:
						await task

					except TimeoutError:
						return
					except Exception as ex:
						on_error_tasks_preparing(ex)
				
				if error_handlyng:
					await error_handlyng

	@property
	def ws(self) -> WebSocketInterface:
		return self._ws


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