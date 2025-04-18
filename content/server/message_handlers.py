from colorama import Fore

from content.shared.dependencies import Ref
from content.shared.messages     import MessageType, MessageModel
from content.shared.utils        import print_notify, NotifyType

async def plug(received_data: Ref[str | bytes]):
	msg_type: MessageType = MessageModel.model_validate_json(received_data.value).type

	print_notify(
		f'Message handl on {Fore.CYAN}{msg_type.name.lower()}{Fore.RESET} not implemented',
		NotifyType.DEBG
	)