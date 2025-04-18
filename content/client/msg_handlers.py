from colorama import Fore
from typing   import Dict

from content.shared.dependencies import Ref, DepencyContainer
from content.shared.messages     import ClientConnectedMessage, ClientDisconnectedMessage
from content.shared.models       import ClientModel
from content.client.shared       import is_client_suitable, print_client


async def on_client_connected(
		received_data: Ref[str | bytes],
		*,
		suitable_clients: Dict[str, ClientModel]
	):
	client: ClientModel = ClientConnectedMessage.model_validate_json(received_data).connected_client
	
	if not is_client_suitable(client):
		return
	
	
	suitable_clients[client.info.user_name] = client
	print_client(client, label=f'{Fore.GREEN}\nНовый пользователь{Fore.RESET}')

async def on_client_disconnected(received_data: Ref[str]):
	client: ClientModel = ClientDisconnectedMessage.model_validate_json(msg).disconnected_client

	
	if client in suitable_clients.values():
		del suitable_clients[client.info.user_name]

		print_notify(f"Пользователь \"{Fore.CYAN}{client.info.user_name}{Fore.RESET}\" отключился", NotifyType.WARN)

async def on_file_forwarding_accept(received_data: Ref[str]):
	pass