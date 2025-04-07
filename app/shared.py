from fastapi.websockets       import WebSocket
from starlette.datastructures import Address
from pydantic                 import BaseModel, field_validator
from enum                     import Enum
from typing                   import Dict
import json

class WorkMode(Enum):
	RECEIVER: int = 0
	SENDER:   int = 1

class ClientState(Enum):
	AWAIT:    int = 0
	RECEIVES: int = 1
	SENDS:    int = 2


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

class MessageType(Enum):
	CLIENT_CONNECTED    = 'client_connected'
	CLIENT_DISCONNECTED = 'client_disconnected'

class MessageModel(BaseModel):
	type: MessageType

class ClientDisconnectedMessageModel(MessageModel):
	disconnected_client: ClientModel

class ClientConnectedMessageModel(MessageModel):
	connected_client: ClientModel