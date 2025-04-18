from colorama import Fore
from typing   import Dict

from content.client.shared       import is_client_suitable, print_client
from content.client.utils        import print_notify, NotifyType
from content.shared.dependencies import Ref, DependencyContainer
from content.shared.messages     import MessageType, MessageModel
from content.shared.messages     import ClientConnectedMessage, ClientDisconnectedMessage, ClientStatusChangedMessage
from content.shared.models       import ClientModel
from content.shared.info         import Info

async def plug(received_data: Ref[str | bytes]):
	msg_type: MessageType = MessageModel.model_validate_json(received_data.value).type

	print_notify(
		f'Message handl on {Fore.CYAN}{msg_type.name.lower()}{Fore.RESET} not implemented',
		NotifyType.DEBG
	)

async def on_client_connected(
		received_data: Ref[str | bytes],
		suitable_clients: Dict[str, ClientModel],
		current_user_info: Info
	):
	client: ClientModel = ClientConnectedMessage.model_validate_json(received_data).connected_client
	
	if not is_client_suitable(client, current_user_info):
		return
	
	
	suitable_clients[client.info.user_name] = client
	print_client(client, label=f'{Fore.GREEN}\nНовый пользователь{Fore.RESET}')


async def on_client_disconnected(
		received_data: Ref[str | bytes],
		suitable_clients: Dict[str, ClientModel]
	):

	client: ClientModel = ClientDisconnectedMessage.model_validate_json(received_data.value).disconnected_client

	if client not in suitable_clients.values():
		return


	del suitable_clients[client.info.user_name]
	print_notify(f"Пользователь \"{Fore.CYAN}{client.info.user_name}{Fore.RESET}\" отключился", NotifyType.WARN)


async def on_client_status_changed(
		received_data: Ref[str | bytes]
	):

	msg = ClientStatusChangedMessage.model_validate_json(received_data)

	print_notify(
		'Статус {client} изменён с {old} на {new}.'
		.format(
			client = f'{Fore.GREEN  }{msg.client.info.user_name}{Fore.RESET}',
			old    = f'{Fore.MAGENTA}{msg.old_state.name       }{Fore.RESET}',
			new    = f'{Fore.CYAN   }{msg.new_state.name       }{Fore.RESET}'
		)
	)
	