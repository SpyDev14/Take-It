from starlette.datastructures import Address
from fastapi.websockets       import WebSocket, WebSocketState
from pydantic                 import ValidationError
from typing                   import Dict, Set
import  copy

from content.server.exceptions import ClientSideError
from content.shared.info_enums import ClientState
from content.shared.messages   import MessageModel
from content.shared.messages   import ClientConnectedMessage, ClientDisconnectedMessage
from content.shared.models     import ClientModel, AddressModel
from content.shared.config     import INVALID_CHARACTERS
from content.shared.info       import Info, is_valid_name
import content.server.messages as MSG
from content.shared.utils import print_notify


class Client:
	def __init__(self, ws: WebSocket, info: Info | None):
		self.ws:    WebSocket   = ws
		self.info:  Info | None = info
		self.state: ClientState = ClientState.AWAIT

	def to_model(self) -> ClientModel:
		client: Address = self.ws.client
		
		return ClientModel(
			info   = self.info.to_model() if self.info else None,
			address = AddressModel(host = client.host, port = client.port),
			state  = self.state
		)
	
class ClientManager:
	def __init__(self):
		self._clients: Dict[str, Client] = dict()
	
	@property
	def clients(self):
		"""Вернёт копию словаря клиентов, а не сам словарь."""
		return copy.copy(self._clients)

	## Sending
	@classmethod
	def __check_message(cls, message: str | MessageModel) -> str:
		"""
		Валидирует и проверяет сообщение.
		В конце возвращает готовое сообщение в виде строки, если всё нормально
		
		:raise TypeError: была получена не строка и не модель.
		:raise ValueError: `message` - не валидная MessageModel модель.
		"""
		
		if not isinstance(message, MessageModel | str):
			raise TypeError(f'Expected MessageModel or str, got {type(message).__name__}')
		
		if isinstance(message, str):
			try:   MessageModel.model_validate_json(message)
			except ValidationError:
				raise ValueError(f'Message \'{message}\' is not valid MessageModel')
			
		elif isinstance(message, MessageModel):
			message: str = message.model_dump_json()
		
		return message
	
	@classmethod
	async def send_personal_message(
			cls,
			client: Client,
			message: str | MessageModel,
			*,
			check_message: bool = True
		) -> None:
		"""Отправит персональное json-сообщение клиенту"""
		
		message: str = cls.__check_message(message)
		
		await client.ws.send_text(message)
	
	@staticmethod
	async def send_personal_data(client: Client, data: bytes) -> None:
		"""Отправит байты клиенту"""
		await client.ws.send_bytes(data)
	
	
	async def broadcast(self, message: str | MessageModel, *, exclude_clients: Set[Client] | None = None) -> None:
		"""
		Отправляет сообщение всем клиентам, кроме тех, кто помечен как исключённый.
		Поддерживает как готовые json, так и `MessageModel`
		"""

		if not self._clients:
			return
		
		message: str = self.__check_message(message)

		for client in self._clients.values():
			if exclude_clients:
				if client in exclude_clients:
					continue

			await self.send_personal_message(client, message, check_message = False)


	## Connection
	@staticmethod
	async def connect(client: Client):
		"""Базовое подключение websocket"""
		await client.ws.accept()
		print_notify(f'connected from {client.ws.client.host}:{client.ws.client.port}')

	async def accept(self, client: Client, info: Info | None = None) -> None:
		"""
		Подтверждение клиента (фактическое подключение)
		
		:raise ValueError: Info не указанно (client.info и info это None)
		:raise ClientSideError: Имя содержит недопустимые символы или клиент с таким именем уже есть
		"""

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
		if client.info.user_name in self._clients:
			raise ClientSideError(
				MSG.NAME_ALREADY_EXISTS.format(
					name = client.info.user_name
				)
			)
		
		await self.broadcast(ClientConnectedMessage(connected_client = client.to_model()))
		self._clients[client.info.user_name] = client


	## Disconnect
	async def on_disconnect(self, client: Client) -> None:
		"""Действия при отключении клиента. Должен быть вызван, если клиент был отключён"""
		# Клиент ещё даже не авторизовался
		if not client.info:
			return
		elif client.info.user_name not in self._clients:
			return
		
		del self._clients[client.info.user_name]
		await self.broadcast(ClientDisconnectedMessage(disconnected_client = client.to_model()))
	
	async def disconnect(
			self,
			client: Client,
			code:   int = 1000,
			reason: str | None = None
		) -> None:
		"""Отключает клиента и вызывает метод `on_disconnect()`"""
		if client.ws.client_state != WebSocketState.DISCONNECTED:
			await client.ws.close(code, reason)

		await self.on_disconnect(client)