from fastapi.websockets import WebSocket, WebSocketDisconnect
from fastapi.responses  import JSONResponse
from fastapi            import FastAPI
from pydantic           import ValidationError
import asyncio, traceback

from content.server.exceptions import ClientSideError
from content.server.client     import Client, ClientManager
# from content.server.config     import FILE_CHUNK_SIZE
from content.shared.messages   import MessageType, MessageHandler, WebSocketInterface
from content.shared.models     import InfoModel, ClientsModel
from content.shared.utils      import print_notify, NotifyType
from content.shared.info       import Info
import content.server.message_handlers as handl
import content.server.messages         as MSG


manager: ClientManager = ClientManager()

## MARK: START
app = FastAPI()

@app.websocket('/ws/')
async def websocket_endpoint(ws: WebSocket):
	client: Client = Client(ws, None)
	await manager.connect(client)
	
	try:
		data: str = await ws.receive_text()

		info_model: InfoModel | None = None
		try:
			info_model = InfoModel.model_validate_json(data)
		except ValidationError:
			await manager.disconnect(client, 1002, MSG.RECEIVED_NOT_INFOMODEL)

		await manager.accept(client, Info.from_model(info_model))

		# MARK: ws.close() теперь использовать НЕЛЬЗЯ!!!
		# Теперь можно использовать ТОЛЬКО метод disconnect(client) экземпляра класса ClientManager!

		message_handler = MessageHandler(
			{
				MessageType.FILE_FORWARDING_REQUEST : handl.on_file_forwarding_request
			},
			
			WebSocketInterface(
				receive = ws.receive_bytes,
				send    = ws.send_bytes
			)
		)

		# ws_message_handling = asyncio.create_task(message_handler.handler())
		# await ws_message_handling

		
	except WebSocketDisconnect:
		await manager.on_disconnect(client)

	except ClientSideError as ex:
		await manager.disconnect(client, 1002, ex.description)
		print_notify(f"{type(ex).__name__}{f': {ex.description}' if ex.description else ''}", NotifyType.ERRO)

	except Exception as ex:
		reason: str = f"{type(ex).__name__}{f': {', '.join(ex.args)}' if len(ex.args) > 0 else ''}"
		await manager.disconnect(client, 1011, reason)
		print_notify(reason, NotifyType.ERRO)
		traceback.print_exc()

@app.get('/clients/')
async def get_clients():
	return JSONResponse(
		ClientsModel(
			clients = { name: client.to_model() for name, client in manager.clients.items() }
		).model_dump(mode='json')
	)