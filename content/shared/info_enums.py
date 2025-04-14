from enum import Enum

class WorkMode(Enum):
	RECEIVER: int = 0
	SENDER:   int = 1

class ClientState(Enum):
	AWAIT:      int = 0
	IN_PROCESS: int = 1