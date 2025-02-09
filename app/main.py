from fastapi import FastAPI, WebSocket, File, UploadFile
from fastapi.responses import HTMLResponse, FileResponse
from enum import Enum
import os

import requests


class WorkMode(Enum):
	SEND = 1
	GET = 0

def is_null_or_whitespace(s: str) -> bool:
	"""
	:param s: Входная строка
	:return: Bool значение, говорящее пустая строка, или нет.
	"""
	return s is None or len(s.strip()) == 0

def incorrect_input():
	print("Неправильный ввод!")
	input()
	os.system("cls")

## START
work_mode: WorkMode = None
username: str = None
info = None

app = FastAPI()

@app.get("/info/")
def get_info():
	return {"message": "Hello", "author": "spy"}

@app.get("/file/")
def get_space_station_servers():
	try:
		json = {}
		return json
	except:
		return {"message": "error"}





























'''
while True:
	answer = input("Выберите режим работы\n 0 - GET\n 1 - SEND\n>>> ").strip().lower()

	if answer in("0", "get"):
		work_mode = WorkMode.GET
		break

	elif answer in("1", "send"):
		work_mode = WorkMode.SEND
		break

	incorrect_input()

while True:
	answer = input("Укажите своё имя: ")

	if is_null_or_whitespace(answer):
		incorrect_input()
		continue

	username = answer
	break


print(f"\nРежим работы: {work_mode}\nИмя пользователя: {username}")
'''


