from fastapi                  import FastAPI
from fastapi.websockets       import WebSocket, WebSocketDisconnect, WebSocketState
from fastapi.responses        import JSONResponse
from starlette.types          import Message
from starlette.datastructures import Address
from typing                   import List, Dict

from shared                   import Info, WorkMode, Client, ClientState
from shared                   import InfoModel, AddressModel, ClientModel, ClientsModel, infomodel_to_info
from shared                   import MessageType, ClientConnectedMessageModel, ClientDisconnectedMessageModel

MSG_RECEIVED_NOT_INFOMODEL = "a json containing an InfoModel was expected, but something else was received."
MSG_NAME_ALREADY_EXISTS    = "such a name \"{name}\" already exists" # Походит на какое-то нарушение, так как это константа
MSG_UNKNOW_ERROR           = "Unknow error"

class ClientManager():
	def __init__(self):
		self.clients: Dict[str, Client] = dict()


	## Connection
	async def connect(self, client: Client) -> bool:
		await client.ws.accept()

	async def accept(self, client: Client, info: Info | None = None) -> bool:
		# инфо нет ни в самом клиенте, ни в аргументах вызова этой функции
		if (client.info is None) and not isinstance(info, Info):
			return False
		
		# клиент.инфо пусто, но в аргументах передали инфо
		if client.info is None and isinstance(info, Info):
			client.info = info
		
		# клиент уже есть в списке
		if client.info.user_name in self.clients:
			await self.disconnect(client, 1002, MSG_NAME_ALREADY_EXISTS.format(name=client.info.user_name))
			return False
		
		await self.broadcast(
			ClientConnectedMessageModel(
				type = MessageType.CLIENT_CONNECTED,
				connected_client = client.to_model()
			).model_dump_json()
		)
		self.clients[client.info.user_name] = client
		return True

	
	## Sending
	async def broadcast(self, msg: str, *, exclude_clients: List[Client] = []):
		if len(self.clients) < 1:
			return

		for client in self.clients.values():
			if client in exclude_clients:
				continue

			await client.ws.send_text(msg)


	## Disconnect
	async def on_disconnect(self, client: Client) -> bool:
		if client.info.user_name not in self.clients:
			return False
		
		del self.clients[client.info.user_name]
		await self.broadcast(
			ClientDisconnectedMessageModel(
				type = MessageType.CLIENT_DISCONNECTED,
				disconnected_client = client.to_model()
			).model_dump_json()
		)
		return True
	
	async def disconnect(self, client: Client, code: int = 1000, reason: str | None = None) -> bool:
		if not client.ws.client_state == WebSocketState.DISCONNECTED:
			await client.ws.close(code, reason)

		await self.on_disconnect(client)
		return True

app = FastAPI()
client_man: ClientManager = ClientManager()

@app.websocket('/ws/')
async def websocket_endpoint(ws: WebSocket):
	client: Client = Client(ws, None)
	await client_man.connect(client)
	
	try:
		data: str = await ws.receive_text()

		info_model: InfoModel | None = None
		try:
			info_model = InfoModel.model_validate_json(data)
		except:
			await client_man.disconnect(client, 1002, MSG_RECEIVED_NOT_INFOMODEL)

		auth_succes: bool = await client_man.accept(client, infomodel_to_info(info_model))
		if not auth_succes and ws.client_state != WebSocketState.DISCONNECTED:
			await ws.close(1011)

		# MARK: ws.close() теперь использовать НЕЛЬЗЯ!!!
		# Теперь можно использовать ТОЛЬКО метод disconnect(client) экземпляра класса ClientManager!
		# Это связанно с тем, что после авторизации client_mann добавляет объект client в
		# список клиентов и если закрыть ws напрямую, метод on_disconnect() вызван не будет
		# и client так и останется в списке клиентов, хотя де-факто он отключён.

		while True:
			data = await ws.receive()
		
	except WebSocketDisconnect:
		await client_man.on_disconnect(client)

	except Exception as ex:
		await client_man.disconnect(client, 1011, ex.args if ex.args else None)

@app.get('/clients/')
async def get_clients():
	return JSONResponse(
		ClientsModel(
			clients = {name: client.to_model() for name, client in client_man.clients.items()}
		).model_dump(mode='json')
	)