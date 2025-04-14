from enum     import Enum
from typing   import Tuple, Set
from colorama import Fore
import asyncio, time

from shared.utils import is_null_or_whitespace

class NotifyType(Enum):
	INFO: str = Fore.CYAN
	DEBG: str = Fore.BLUE
	WARN: str = Fore.YELLOW
	ERRO: str = Fore.RED
	FATL: str = Fore.MAGENTA

notify_shell: str = '[{0}]'
def print_notify(
		message: str,
		notify_type: NotifyType = NotifyType.INFO,
		start_with = '\r',
		ends_with='\n'
	) -> str:

	msg = f"{start_with}{notify_shell.format(f'{notify_type.value}{notify_type.name}{Fore.RESET}')} {message}"

	print(msg, end=ends_with)
	return msg

class PreparedAnimations(Enum):
	LINE:    Tuple[str] = ('|', '/', '-', '\\')
	POINTS:  Tuple[str] = ('.  ', '.. ', '...')
	CIRCLE:  Tuple[str] = ('◜','◝','◞','◟')
	BLOCK:   Tuple[str] = ('▌','▀','▐','▄')
	FILLING: Tuple[str] = ('▁▂▃▅▆█')

# MARK: мб, потом сделаю класс "AnimationSettings" и enum "PreparedAnimations" (с другим названием)
# MARK: Может стоит добавить bool "очищать строку после завершения"?
async def play_simbol_animation(
		text: str | None = None,
		*,
		anim_shots: Tuple[str] | PreparedAnimations = PreparedAnimations.LINE,
		anim_speed: float = 2.5,
		indent: str = ' ',
		close_anim_with: str = '',
		force_shot_time: float | None = None
	):

	"""
	Должна запускаться в асинхронной task:
	```python
	task = asyncio.create_task(play_onechar_animation())
	```
	
	Для корректного завершения работы, должна завершаться следующим образом:
	```python
	task.cancel()
	await task
	```

	Либо можно использовать `async with asyncio.TaskGroup()` и в конце писать только
	`task.cancel()`, а ожидание завершения задачи произойдёт автоматически.

	:param text: Текст перед анимацией: `"Поиск..." /` (отступ между текстом и анимацией определяется `indent`)
	:param anim_shots: Кадры анимации в ввиде Tuple[str], или из заранее заготовленных.
	:param anim_speed: Сколько раз в секунду проигрывать анимацию? (Зависит от количества кадров)
	:param close_anim_with: Какой символ будет выведен, после окончания анимации?
	(Если нужно, чтобы в конце был символ новой строки, например)
	
	:param indent: Символ отступа между текстом и анимацией
	:param force_shot_time: Форсирует время одного кадра (проигнорирует `anim_speed`)
	"""
	if isinstance(anim_shots, PreparedAnimations):
		anim_shots = anim_shots.value 

	if len(anim_shots) < 2:
		if len(anim_shots) < 1:
			print_notify("Anim err: to many shots", NotifyType.ERRO)
			return

		anim_shots = tuple(anim_shots[0])
	
	if anim_speed <= 0:
		print_notify("Anim err: speed can't be <= 0")
		return

	shot_time: float = (1 / anim_speed) / len(anim_shots) if not force_shot_time else force_shot_time

	text = f"{text.strip()}{indent}" if not is_null_or_whitespace(text) else ''
	try:
		while True:
			for shot in anim_shots:
				print(f"\r{text}{shot}", end='', flush=True)
				await asyncio.sleep(shot_time)

	except asyncio.CancelledError:
		# Очистка строки
		print(f"\r{' '*(len(text)+max(map(len, anim_shots)))}\r", end=close_anim_with, flush=True)

##MARK: START
if __name__ == '__main__':
	msg: str = "lazy dog"
	print_notify(msg)
	print_notify(msg, NotifyType.DEBG)
	print_notify(msg, NotifyType.WARN)
	print_notify(msg, NotifyType.ERRO)

	async def func():
		for anim in PreparedAnimations:
			anim_task = asyncio.create_task(play_simbol_animation(f"{anim.name}:", anim_shots=anim))
			await asyncio.sleep(5)
			anim_task.cancel()
			await anim_task
	asyncio.run(func())