from typing import Callable, List, Dict, Awaitable
from colorama import Fore, Style
import asyncio, copy, dis

from content.shared.dependencies import DependencyContainer, Ref
from content.shared.info_enums   import WorkMode
from content.shared.utils        import print_notify, NotifyType
from content.shared.info         import Info

from content.client.command_handling import CommandHandler

ex = Exception('Что-то')
print(type(ex).__name__)