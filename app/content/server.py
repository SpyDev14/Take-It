from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.types import Message

app = FastAPI()

@app.get('takeit/info/')
async def get_info():
	return {}

@app.websocket('takeit/ws/{client_id}')
async def websocket_endpoint(websocket: WebSocket, client_id: int):
	await websocket.accept()
	try:
		while True:
			data: Message = websocket.receive()
	except WebSocketDisconnect:
		pass
