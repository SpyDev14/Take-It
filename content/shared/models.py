from pydantic import BaseModel
from datetime import datetime
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
	
# Время в формате ISO
class FileInfoModel(BaseModel):
	name:          str
	byte_size:     int
	creation_time: str
	modified_time: str
	access_time:   str
	# attributes: int
	# owner: str
	hash_summ:     str

class FileChunkInfoModel(BaseModel):
	file: FileInfoModel
	chunks_count: int
	chunk:        int