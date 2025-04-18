from typing import Callable, Any, Dict, List, Set, Generic, Type, TypeVar
from enum   import Enum
import inspect

from content.shared.exceptions import MissingDepencyError, ImmutableDependencyTypeError

_T = TypeVar('T')

class Ref(Generic[_T]):
	__slots__ = ('value')

	def __init__(self, value: _T):
		self.value: _T = value

	def __str__(self):
		return self.value.__str__()
	
del _T

class DepencyContainer():
	'''
	Предстовляет собой словарь ссылок на объекты с дополнительными методами.
	Нужен для удобного управления зависимостями обработчиков.

	#### Зависимости по умолчанию:
		`this_dependency_container: DepencyContainer` - объект этого контейнера зависимостей.

	### Неизменяемые типы не поддерживаются:
	```
	bool, int, float, complex, tuple, str, frozenset, bytes
	```
	Используйте `Ref()` обёртку для подобных типов.
	Это связанно с тем, что на неизменяемые типы не может быть ссылок,
	а DependencyContainer - это именованный список ссылок.

	:raise ImmutableDependencyTypeError: В конструктор был передан неизменяемый тип, который несовместим с DependencyContainer.
	'''

	# Неизменяемые типы, т.е те, при присваивании которых получается копия, а не ссылка
	# x = 10; y = x;    y is x   == False <- копирование
	# arr = [1,2,3]
	# arr2 = arr   ; arr2 is arr == True  <- создание ссылки, подходит
	_IMMUTABLE_TYPES: Set[Type] = (
		bool,
		int,
		float,
		complex,
		tuple,
		str,
		frozenset,
		bytes,
		None
	)

	def __check_dependency_object_type_mutable(cls, name, dependency):
		'''
		Проверяет поддерживаемость типа объекта. Выкидывает исключение, если тип неизменяемый.

		:param name:       Имя зависимости
		:param dependency: Объект зависимости для проверки.

		:raise ImmutableDependencyTypeError: Тип неизменяем => неподдерживается.
		'''
		if type(dependency) in cls._IMMUTABLE_TYPES:
			raise ImmutableDependencyTypeError(
				f"Object '{name}' is immutable, so it can't be here. Use Ref() class for make his mutable. Immutable (unsupported) types: {', '.join(cls._IMMUTABLE_TYPES)}"
			)

	def __init__(self, **dependencies):
		for name, dependency in dependencies.items():
			self.__check_dependency_object_type_mutable(name, dependency)
		
		dependencies['this_dependency_container'] = self
		self._dependencies: Dict[str, Any] = dependencies

	def __len__(self):
		return len(self._dependencies)
	
	def __contains__(self, depency):
		return depency in self._dependencies
	
	
	def add(self, **new_dependencies):
		'''
		Добавляет зависимости в контейнер. В качестве значения необходимо указывать ссылку, а не значение.

		:raise KeyError: Одна или несколько зависимостей с таким именем уже есть
		'''

		conflict_dependencies:  List[str] = []
		dependencies_to_adding: Dict[str, Any] = {}

		for name, new_dependency in new_dependencies.items():
			self.__check_dependency_object_type_mutable(name, new_dependency)

			if name in self._dependencies:
				conflict_dependencies.append(name)
				continue

			dependencies_to_adding[name] = new_dependency
		
		if conflict_dependencies:
			raise KeyError(
				f"Depency '{conflict_dependencies[0]}' is already there" if len(conflict_dependencies) == 1
				else f"The dependencies {', '.join(conflict_dependencies)} already exist."
			)

		self._dependencies.update(dependencies_to_adding)

	def remove(self, name: str):
		'''
		Удаляет зависимость

		:raise KeyError: Зависимости не существует
		'''

		if name not in self._dependencies:
			raise KeyError(f"Dependency '{name}' does not exist")
		
		del self._dependencies[name]


	def get(self, name: str) -> Any | None:
		'''Возвращает зависимость по имени. Вернёт `None`, если такой зависимости нет.'''

		return self._dependencies.get(name.strip())
	

	def resolve(self, customer: Callable):
		required_dependencies: Dict[str, Any] = dict()
		missing_dependencies:  List[str]      = list()

		for required_depency in inspect.signature(customer).parameters:
			if required_depency not in self._dependencies:
				missing_dependencies.append(required_depency)
				continue
				
			required_dependencies[required_depency] = self._dependencies[required_depency]
			
		if missing_dependencies:
			raise MissingDepencyError(f"Necessary dependencies are missing: {', '.join(missing_dependencies)}.\n" +
			f"Available dependencies:\n{'\n'.join(self._dependencies)}"
			)

		return required_dependencies