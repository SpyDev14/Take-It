from info import WorkMode, Info
from utils import is_null_or_whitespace
from fastapi import FastAPI, WebSocket

def incorrect_input():
	print("Неправильный ввод!")
	input()

## START
work_mode: WorkMode = None
user_name: str = None
info: Info = None

print(f"\nДобро пожаловать в Take It!\n")
 
while True:
	answer = input("Выберите режим работы\n 0 - GET\n 1 - SEND\n>>> ").strip().lower()

	if answer in ("0", "get", 'g'):
		work_mode = WorkMode.GET
		break

	elif answer in ("1", "send", 's'):
		work_mode = WorkMode.SEND
		break


	incorrect_input()

while True:
	answer = input("Укажите своё имя: ")

	if is_null_or_whitespace(answer):
		incorrect_input()
		continue

	user_name = answer
	break

info = Info(user_name, work_mode)
del user_name, work_mode

