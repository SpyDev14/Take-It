from typing import Callable, List, Dict, Awaitable
from colorama import Fore, Style
import asyncio, copy

from content.shared.dependencies import DependencyContainer, Ref
from content.shared.info_enums   import WorkMode
from content.shared.utils        import print_notify, NotifyType
from content.shared.info         import Info

from content.client.command_handling import CommandHandler

"""
async def echo_command(raw_user_input: Ref[str]):
	user_input: str = raw_user_input.value

	command_name: str = user_input.split(' ')[0]
	print(user_input.removeprefix(command_name).strip())

async def eval_command(raw_user_input: Ref[str]):
	user_input: str = raw_user_input.value

	command_name: str = user_input.split(' ')[0]
	result = eval(user_input.removeprefix(command_name).strip())

	if result: print(result)

async def print_my_info_command(user_info: Info):
	print(f'''
	user: {user_info.user_name}
	mode: {user_info.work_mode}
''')
	
async def set_my_info_command(user_info: Info):
	user_info.user_name = input('Name: ')
	user_info.work_mode = WorkMode.SENDER if input('Mode: ') == 'sender' else WorkMode.RECEIVER
	
async def python_command():
	while True:
		user_input: str = input(f'{Fore.GREEN}(py){Fore.RESET}{Fore.MAGENTA} >>> {Fore.RESET}')
		if user_input in ('exit', 'break'):
			break
		
		result = eval(user_input)
		if result: print()

async def print_funny_number_command(funny_number: int):
	print(f'Funny number is: {Fore.GREEN}{funny_number}{Fore.RESET}')

async def set_funny_number_command(funny_number: Ref[int], raw_user_input: Ref[str]):
	args: List[str] = raw_user_input.value.split(' ')
	args.remove('set_funny_number')
	funny_number.value = int(args[0])

commands: Dict[Callable, str] = {
	echo_command:   'Выведет указанный текст на экран',
	eval_command:   'Выполнит строку интерпретатором python',
	python_command: 'Запустит eval в цикле',
	print_my_info_command: 'Выведет информацию о пользователе',
	  set_my_info_command: 'Установит информацию о пользователе',
	print_funny_number_command: 'Выведет на экран забавное число',
	  set_funny_number_command: 'Установит забавное число'
}

async def help_command(raw_user_input: Ref[str]):
	print(
		'\n'.join(
			sorted(
				{
					f"{Fore.GREEN}{Style.BRIGHT}{command.__name__.removesuffix('_command')}{Style.RESET_ALL}{Fore.RESET}: {desc}"
					for command, desc in commands.items()
				}
			)
		)
	)

commands[help_command] = 'Выводит информацию о командах'

funny_number = Ref(123)
ch = CommandHandler(
	{
		command.__name__.removesuffix('_command'): command
		for command in commands
	},

	dependencies = DependencyContainer(
		user_info = Info('Чувак', WorkMode.RECEIVER),
		funny_number = funny_number
	)
)


asyncio.run(ch.handler())
"""
pivo_type: Ref[str] = Ref('svetloe')
pivo_count: Ref[int] = Ref(10)
deps: DependencyContainer = DependencyContainer(pivo_type = pivo_type)

copy_deps = copy.copy(deps)
copy_deps.add(pivo_count = pivo_count)

print(f'''
deps = {deps}
copy = {copy_deps}

count = {pivo_count}
type  = {pivo_type}
 
count in deps: {pivo_count in deps}
count in copy: {pivo_count in copy_deps}

type in deps: {pivo_type in deps}
type in copy: {pivo_type in copy_deps}
''')

pivo_type.value = 'temnoe'
pivo_count.value = 5

print(f'''
deps = {deps}
copy = {copy_deps}

count = {pivo_count}
type  = {pivo_type}
 
count in deps: {pivo_count in deps}
count in copy: {pivo_count in copy_deps}

type in deps: {pivo_type in deps}
type in copy: {pivo_type in copy_deps}
''')