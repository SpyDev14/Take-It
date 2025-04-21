from pydantic import BaseModel
from datetime import datetime as DateTime
from typing   import Dict

from content.shared.info_enums import WorkMode, ClientState

class InfoModel(BaseModel):
	user_name: str
	work_mode: WorkMode

class AddressModel(BaseModel):
	host: str
	port: int

class ClientModel(BaseModel):
	info:    InfoModel | None
	address: AddressModel
	state:   ClientState

class ClientsModel(BaseModel):
	clients: Dict[str, ClientModel]
	
class FileInfoModel(BaseModel):
	name:             str
	byte_size:        int
	created_time:     DateTime
	modified_time:    DateTime
	last_access_time: DateTime
	owner:            str