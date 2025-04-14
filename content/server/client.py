from starlette.datastructures import Address
from fastapi.websockets       import WebSocket, WebSocketState
from typing                   import Dict, Set

from content.server.exceptions import ClientSideError
from content.shared.info_enums import ClientState
from content.shared.messages   import MessageModel
from content.shared.messages   import ClientConnectedMessage, ClientDisconnectedMessage
from content.shared.models     import ClientModel, AddressModel
from content.shared.config     import INVALID_CHARACTERS
from content.shared.info       import Info, is_valid_name
import content.server.messages as MSG

class Client():
	def __init__(self, ws: WebSocket, info: Info | None):
		self.ws:    WebSocket   = ws
		self.info:  Info | None = info
		self.state: ClientState = ClientState.AWAIT

	def to_model(self) -> ClientModel:
		client: Address = self.ws.client
		
		return ClientModel(
			info   = self.info.to_model() if self.info else None,
			adress = AddressModel(host = client.host, port = client.port),
			state  = self.state
		)
	
class ClientManager():
	def __init__(self):
		self.clients: Dict[str, Client] = dict()


	## Sending
	async def send_personal_message(self, client: Client, msg: str) -> None:
		'''Отправит персональное текстовое сообщение клиенту'''
		await client.ws.send_text(msg)

	async def send_bytes(self, client: Client, bytes) -> None:
		pass

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
				MSG.INVALID_NAME.format(
					name = client.info.user_name,
					inval_chars = INVALID_CHARACTERS
				)
			)

		# ERRO: клиент уже есть в списке
		if client.info.user_name in self.clients:
			raise ClientSideError(
				MSG.NAME_ALREADY_EXISTS.format(
					name = client.info.user_name
				)
			)
					
		
		await self.broadcast(
			ClientConnectedMessage(
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
		# await self.broadcast(
		# 	ClientDisconnectedMessage(
		# 		disconnected_client = client.to_model()
		# 	)
		# )
	
	async def disconnect(self, client: Client, code: int = 1000, reason: str | None = None) -> None:
		'''Отключает клиента. Вызывает метод `on_disconnect()`'''
		if client.ws.client_state != WebSocketState.DISCONNECTED:
			print("Всё работает окэй")
			await client.ws.close(code, reason)

		await self.on_disconnect(client)