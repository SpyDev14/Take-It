from fastapi.websockets       import WebSocket
from starlette.datastructures import Address
from pydantic                 import BaseModel, model_validator, Field
from enum                     import Enum
from typing                   import Dict, Set, Callable, Awaitable, Any, ClassVar, Literal
import asyncio

INVALID_CHARACTERS: Set[str] = {'\\', '/', ':', '?', '"', '<', '>', '|'}

def is_valid_name(name: str) -> bool:
	for char in list(name):
		if char in INVALID_CHARACTERS:
			return False
	return True

class WorkMode(Enum):
	RECEIVER: int = 0
	SENDER:   int = 1

class ClientState(Enum):
	AWAIT:      int = 0
	IN_PROCESS: int = 1

class InfoModel(BaseModel):
	user_name: str
	work_mode: WorkMode
# The function to convert this to Info is described below

class Info():
	def __init__(self, user_name: str, work_mode: WorkMode):
		self.user_name: str = user_name
		self.work_mode: WorkMode = work_mode

	def to_model(self) -> InfoModel:
		return InfoModel(
			user_name = self.user_name,
			work_mode = self.work_mode
		)

def infomodel_to_info(model: InfoModel) -> Info: return Info(model.user_name, model.work_mode)

class AddressModel(BaseModel):
	host: str
	port: int

class ClientModel(BaseModel):
	info:   InfoModel | None
	adress: AddressModel
	state:  ClientState

class ClientsModel(BaseModel):
	clients: Dict[str, ClientModel]

class Client():
	def __init__(self, ws: WebSocket, info: Info | None):
		self.ws:    WebSocket = ws
		self.info:  Info | None = info
		self.state: ClientState = ClientState.AWAIT

	def to_model(self) -> ClientModel:
		client: Address = self.ws.client
		
		return ClientModel(
			info   = self.info.to_model() if self.info else None,
			adress = AddressModel(host = client.host, port = client.port),
			state  = self.state
		)


## MARK: Messages:
class MessageType(Enum):
	CLIENT_CONNECTED      = 'client_connected'
	CLIENT_DISCONNECTED   = 'client_disconnected'
	CLIENT_STATUS_CHANGED = 'client_status_changed'

	SEND_FILE_CHUNK = 'send_file_chunk'

class MessageModel(BaseModel):
	_type: ClassVar[MessageType]
	type: MessageType = Field(frozen=True)

	@model_validator(mode='after')
	def _validate_type(self):
		if self.type != self.__class__._type:
			raise ValueError(f'type must be a {self.__class__._type}, but he\'s {self.type}')

class MessageHandler():
	def __init__(
			self,
			message_handlers: Dict[MessageType, Callable[[str], None]],
			ws_receive: Callable[[], Awaitable[Any]]
		):

		self._MESSAGE_HANDLERS: Dict[MessageType, Callable[[str], None]] = message_handlers
		self.ws_receive:        Callable[[], Awaitable[Any]]             = ws_receive		

	async def handler(self):
		type: MessageType
		msg: str

		task = None
		
		try:
			while True:
				msg  = await self.ws_receive()
				type = MessageModel.model_validate_json(msg).type

				if type not in self._MESSAGE_HANDLERS:
					continue

				task = asyncio.create_task(self._MESSAGE_HANDLERS[type](msg))
				await task

		except asyncio.CancelledError:
			if task:
				await task


class ClientDisconnectedMessageModel(MessageModel):
	_type =       MessageType.CLIENT_DISCONNECTED
	type: Literal[MessageType.CLIENT_DISCONNECTED] = Field(default=_type, frozen=True)

	disconnected_client: ClientModel

class ClientConnectedMessageModel(MessageModel):
	_type =       MessageType.CLIENT_CONNECTED
	type: Literal[MessageType.CLIENT_CONNECTED] = Field(default=_type, frozen=True)

	connected_client: ClientModel

class ClientStatusChangedMessageModel(MessageModel):
	_type =       MessageType.CLIENT_STATUS_CHANGED
	type: Literal[MessageType.CLIENT_STATUS_CHANGED] = Field(default=_type, frozen=True)

	client:    ClientModel
	new_state: ClientState
	old_state: ClientState

class ClientStatusChangedMessageModel(MessageModel):
	_type =       MessageType.SEND_FILE_CHUNK
	type: Literal[MessageType.SEND_FILE_CHUNK] = Field(default=_type, frozen=True)

	receiver: ClientModel
	sender:   ClientModel

	# file info...


## MARK: Exceptions:
class ClientSideError(Exception):
	'''Общее исключение для ошибок со стороны клиента'''
	def __init__(self, description: str | None = None, *args):
		super().__init__(*args)

		self.description: str | None = description

## MARK: MAIN
if __name__ == '__main__':
	class Pivo():
		host: str = '127.0.0.1'
		port: int = 8000

	class Parasha():
		client: Pivo = Pivo()

	cdmm = ClientDisconnectedMessageModel(disconnected_client = Client(Parasha(), Info('', 0)).to_model())
	ccmm = ClientConnectedMessageModel   (   connected_client = Client(Parasha(), Info('', 0)).to_model())

	print(f'''
{cdmm.type} : {cdmm._type}
{ccmm.type} : {ccmm._type}
''')