from fastapi                  import FastAPI
from fastapi.websockets       import WebSocket, WebSocketDisconnect, WebSocketState
from fastapi.responses        import JSONResponse
from starlette.types          import Message
from starlette.datastructures import Address
from typing                   import List, Dict, Set
import asyncio

from shared import Info, WorkMode, Client, ClientState
from shared import InfoModel, AddressModel, ClientModel, ClientsModel, infomodel_to_info
from shared import MessageType, ClientConnectedMessageModel, ClientDisconnectedMessageModel, MessageModel
from shared import INVALID_CHARACTERS, is_valid_name
from shared import MessageHandler
from shared import ClientSideError


MSG_RECEIVED_NOT_INFOMODEL = "a json containing an InfoModel was expected, but something else was received."
MSG_NAME_ALREADY_EXISTS    = "such a name \"{name}\" already exists"
MSG_INVALID_NAME           = "the name \"{name}\" does not meet the standard and contains invalid characters ({inval_chars})."
MSG_UNKNOW_ERROR           = "Unknow error"

## MARK: CLIENT MANAGER
class ClientManager():
	def __init__(self):
		self.clients: Dict[str, Client] = dict()


	## Sending
	async def send_personal_message(self, client: Client, msg: str) -> None:
		'''Отправит персональное текстовое сообщение клиенту'''
		await client.ws.send_text(msg)

	async def broadcast(self, msg: str | MessageModel, *, exclude_clients: Set[Client] = set()) -> None:
		'''Отправляет сообщение всем клиентам, кроме тех, кто помечен как исключённый.
		Поддерживает как готовые json, так и `MessageModel`'''

		if len(self.clients) < 1:
			return
		
		if isinstance(msg, MessageModel):
			msg = msg.model_dump_json()

		else:
			MessageModel.model_validate_json(msg)

		for client in self.clients.values():
			if client in exclude_clients:
				continue

			await self.send_personal_message(client, msg)


	## Connection
	async def connect(self, client: Client):
		'''Базовое подключение websocket'''
		await client.ws.accept()
		print(f'> from {client.ws.client.host}:{client.ws.client.port}')

	async def accept(self, client: Client, info: Info | None = None) -> None:
		'''Подтверждение клиента (фактическое подключение)'''
		# ERRO: info нет ни в самом клиенте, ни в аргументах вызова этой функции
		if (client.info is None) and not isinstance(info, Info):
			raise ValueError('info нет ни в client, ни в аргументах')
		
		# client.info пусто, но в аргументах передали info
		if client.info is None and isinstance(info, Info):
			client.info = info
		
		# ERRO: имя содержит недопустимые символы
		if not is_valid_name(client.info.user_name):
			raise ClientSideError(
				MSG_INVALID_NAME.format(
					name = client.info.user_name,
					inval_chars = INVALID_CHARACTERS
				)
			)

		# ERRO: клиент уже есть в списке
		if client.info.user_name in self.clients:
			raise ClientSideError(
				MSG_NAME_ALREADY_EXISTS.format(
					name = client.info.user_name
				)
			)
					
		
		await self.broadcast(
			ClientConnectedMessageModel(
				connected_client = client.to_model()
			)
		)
		self.clients[client.info.user_name] = client


	## Disconnect
	async def on_disconnect(self, client: Client) -> None:
		'''Действия при отключении клиента. Должен быть вызван, если клиент фактически отключён'''
		if client.info.user_name not in self.clients:
			return
		
		del self.clients[client.info.user_name]
		await self.broadcast(
			ClientDisconnectedMessageModel(
				disconnected_client = client.to_model()
			)
		)
	
	async def disconnect(self, client: Client, code: int = 1000, reason: str | None = None) -> None:
		'''Отключить клиента. Также вызывает метод `on_disconnect()`'''
		if not client.ws.client_state == WebSocketState.DISCONNECTED:
			await client.ws.close(code, reason)

		await self.on_disconnect(client)

manager: ClientManager = ClientManager()

## MARK: Message handlers:
async def on_send_file_chunk(msg: str) -> None:
	pass




## MARK: START
app = FastAPI()

@app.websocket('/ws/')
async def websocket_endpoint(ws: WebSocket):
	client: Client = Client(ws, None)
	await manager.connect(client)
	
	try:
		data: str = await ws.receive_text()

		info_model: InfoModel | None = None
		try:
			info_model = InfoModel.model_validate_json(data)
		except:
			await manager.disconnect(client, 1002, MSG_RECEIVED_NOT_INFOMODEL)


		await manager.accept(client, infomodel_to_info(info_model))

		# MARK: ws.close() теперь использовать НЕЛЬЗЯ!!!
		# Теперь можно использовать ТОЛЬКО метод disconnect(client) экземпляра класса ClientManager!
		

		message_handler = MessageHandler(
			{
				MessageType.SEND_FILE_CHUNK : on_send_file_chunk
			},
			ws.receive
		)

		ws_message_handling = asyncio.create_task(message_handler.handler())
		await ws_message_handling
		
	except WebSocketDisconnect:
		await manager.on_disconnect(client)

	except ClientSideError as ex:
		await manager.disconnect(client, 1002, ex.description)

	except Exception as ex:
		await manager.disconnect(client, 1011, ex.args if ex.args else None)

@app.get('/clients/')
async def get_clients():
	return JSONResponse(
		ClientsModel(
			clients = { name: client.to_model() for name, client in manager.clients.items() }
		).model_dump(mode='json')
	)