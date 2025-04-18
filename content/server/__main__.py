from fastapi.websockets import WebSocket, WebSocketDisconnect
from fastapi.responses  import JSONResponse
from fastapi            import FastAPI
import asyncio

from content.server.exceptions import ClientSideError
from content.server.client     import Client, ClientManager
from content.server.config     import FILE_CHUNK_SIZE
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
		except:
			await manager.disconnect(client, 1002, MSG.RECEIVED_NOT_INFOMODEL)


		await manager.accept(client, Info.from_model(info_model))

		# MARK: ws.close() теперь использовать НЕЛЬЗЯ!!!
		# Теперь можно использовать ТОЛЬКО метод disconnect(client) экземпляра класса ClientManager!

		message_handler = MessageHandler(
			{
				MessageType.FILE_FORWARDING_REQUEST : handl.plug
			},
			
			WebSocketInterface(
				receive = ws.receive,
				send    = ws.send
			)
		)

		ws_message_handling = asyncio.create_task(message_handler.handler())
		raise Exception('копатыча мобилизировали на сво!!!')
		await ws_message_handling

		
	except WebSocketDisconnect:
		await manager.on_disconnect(client)

	except ClientSideError as ex:
		await manager.disconnect(client, 1002, ex.description)
		print_notify(ex, NotifyType.ERRO)

	except Exception as ex:
		await manager.disconnect(client, 1011, ex.args if ex.args else None)
		print_notify(ex, NotifyType.ERRO)

@app.get('/clients/')
async def get_clients():
	return JSONResponse(
		ClientsModel(
			clients = { name: client.to_model() for name, client in manager.clients.items() }
		).model_dump(mode='json')
	)