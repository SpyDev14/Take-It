from enum import Enum

class WorkMode(Enum):
	RECEIVER: str = 'receiver'
	SENDER:   str = 'sender'

class ClientState(Enum):
	AWAIT:      str = 'await'
	IN_PROCESS: str = 'in_progress'