from enum     import Enum
from typing   import Tuple
from colorama import Fore
import asyncio

from content.shared.utils import is_null_or_whitespace, print_notify, NotifyType

class PreparedAnimations(Enum):
	LINE:    Tuple[str] | str = ('|', '/', '-', '\\')
	POINTS:  Tuple[str] | str = ('.  ', '.. ', '...')
	CIRCLE:  Tuple[str] | str = ('◜','◝','◞','◟')
	BLOCK:   Tuple[str] | str = ('▌','▀','▐','▄')
	FILLING: Tuple[str] | str = '▁▂▃▅▆█'

# MARK: мб, потом сделаю класс "AnimationSettings" и enum "PreparedAnimations" (с другим названием)
# MARK: Может, стоит добавить bool "очищать строку после завершения"?
async def play_symbol_animation(
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
	task = asyncio.create_task(play_symbol_animation())
	```
	
	Для корректного завершения работы, должна завершаться следующим образом:
	```python
	task.cancel()
	await task
	```

	Либо можно использовать `async with asyncio.TaskGroup()` и в конце писать только
	`task.cancel()`, а ожидание завершения задачи произойдёт автоматически.

	:param text: Текст перед анимацией: `"Поиск..." /` (отступ между текстом и анимацией определяется `indent`)
	:param anim_shots: Кадры анимации в виде Tuple[str], или из заранее заготовленных.
	:param anim_speed: Сколько раз в секунду проигрывать анимацию? (Зависит от количества кадров)
	:param close_anim_with: Какой символ будет выведен, после окончания анимации?
	(Если нужно, чтобы в конце был символ новой строки, например)
	
	:param indent: Символ отступа между текстом и анимацией
	:param force_shot_time: Форсирует время одного кадра (проигнорирует `anim_speed`)
	"""
	try:
		if isinstance(anim_shots, PreparedAnimations):
			anim_shots = anim_shots.value
			
		if isinstance(anim_shots, str):
			anim_shots = tuple(anim_shots)
			
	
		if len(anim_shots) < 2:
			raise ValueError("to many shots")
		
		if anim_speed <= 0:
			raise ValueError("animation speed must be > 0")
		
	except ValueError as e:
		print_notify(f"Anim error: {e}", NotifyType.ERRO)
		return

	shot_time: float = (1 / anim_speed) / len(anim_shots) if not force_shot_time else force_shot_time

	text = f"{text.strip()}{indent}" if not is_null_or_whitespace(text) else ''
	try:
		while True:
			for shot in anim_shots:
				print(f"\r{text}{shot}", end = '', flush = True)
				await asyncio.sleep(shot_time)

	except asyncio.CancelledError:
		# Очистка строки
		print(f"\r{' '*(len(text)+max(map(len, anim_shots)))}\r", end = close_anim_with, flush = True)



##MARK: START
if __name__ == '__main__':
	msg: str = "lazy dog"
	print_notify(msg)
	print_notify(msg, NotifyType.DEBG)
	print_notify(msg, NotifyType.WARN)
	print_notify(msg, NotifyType.ERRO)

	async def func():
		for anim in PreparedAnimations:
			anim_task = asyncio.create_task(play_symbol_animation(f"{anim.name}:", anim_shots=anim))
			await asyncio.sleep(5)
			anim_task.cancel()
			await anim_task
	asyncio.run(func())