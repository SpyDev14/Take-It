from typing import Callable, Any, Dict, List, Set, Generic, Type, TypeVar, Self, Awaitable
import inspect, copy

from content.shared.exceptions import MissingDependencyError, DependencyCannotBeImmutableType

_T = TypeVar('_T')

class Ref(Generic[_T]):
	"""
	Является классом-обёрткой для "создания ссылок" на неизменяемые типы (`int`, `str`, `bool`, `tuple`, ...).
	Нужен для работы с `DependencyContainer`. Создать ссылку на уже существующий неизменяемый объект с помощью
	него не получится, так как при создании такой объект скопируется в аргументы конструктора.

	## Осторожно!
	Значение находится в поле `value`! Ref - объект с полем `value`! (Можно запутаться)
	```
	num = Ref(5)

	num == 5 # False
	num.value == 5 # True
    ```

	### Пример создания:
	```
	num: int = 4
	ref_num: Ref[int] = Ref(num) # Не сработает, конструктор получит копию num

	print(ref_num.value is num) # False (так не работает)

	good_num: Ref[int] = Ref(4)
	ref_good_num = good_num

	print(good_num.value is ref_good_num.value) # True
	```

	### Более подробный пример (с применением):
	```
		persons: List[str] = ['pers1', 'pers2'] # <- Изменяемый тип по умолчанию, т.е передав его в качестве аргумента будет передана ссылка на этот объект (далее ссылочный тип).
		sample_num: int = 3 # <- Неизменяемый тип. При передачи в качестве аргумента получится новый объект (далее значимый тип).

		deps = DependencyContainer(
			persons = persons,
			copy_of_sample_num = Ref(sample_num) # <- Мы создали копию sample_num, но copy_of_sample_num уже будет ссылочным объектом.
		)
		
		print(sample_num is deps.get('copy_of_sample_num').value) # False (в контейнере копия)
		print(persons    is deps.get('persons')) # True (в контейнере ссылка)

		funny_number: Ref[int | None] = Ref(None) # Сразу создаём ссылочный объект

		while not funny_number.value:
			try:
				funny_number.value = int(input('funny_number>>> '))
			except: pass

		deps.add(funny_number = funny_number) # funny_number - ссылочный объект, он нам подходит, можем добавить в DC
		print(funny_number is deps.get('funny_number')) # True (в контейнере ссылка)
	```
	"""

	__slots__ = 'value'

	def __init__(self, value: _T):
		self.value: _T = value

	def __str__(self):
		return self.value.__str__()
	
del _T

class DependencyContainer:
	"""
	Представляет собой словарь ссылок на объекты с дополнительными методами.
	Нужен для удобного управления зависимостями обработчиков.

	#### Зависимости по умолчанию:
		`this_dependency_container: DependencyContainer` - объект этого контейнера зависимостей.

	### Неизменяемые типы не поддерживаются:
	```
	bool, int, float, complex, tuple, str, frozenset, bytes, range, None
	```
	Используйте `Ref()` обёртку для подобных типов.
	Это связанно с тем, что на неизменяемые типы не может быть ссылок,
	а DependencyContainer - это именованный список ссылок.

	#### Пример использования:
	```
		# `Ref` - обёртка для создания ссылки
		def funny_func(bottles_count: Ref[int], persons: List[str])
			pass
		
		dependencies = DependencyContainer(
			bottles_count = Ref(12),
			persons = ['Oleg', 'Pavel', 'Nekitos']
		)

		funny_func(**dependencies.resolve(funny_func))
	```

	:raise ImmutableDependencyTypeError: В конструктор был передан объект
	неизменяемого типа, который несовместим с DependencyContainer.
	"""

	# Неизменяемые типы, т.е те, при присваивании которых получается копия, а не ссылка
	# Для работы с ними нужно использовать Ref()
	_IMMUTABLE_TYPES: Set[Type] = (
		frozenset,
		complex,
		bytes,
		float,
		tuple,
		range,
		bool,
		None,
		int,
		str
	)

	def __check_dependency_object_type_mutable(self, name, dependency):
		"""
		Проверяет поддерживаемость типа объекта. Выкидывает исключение, если тип неизменяемый.

		:param name:       Имя зависимости
		:param dependency: Объект зависимости для проверки.

		:raise ImmutableDependencyTypeError: Тип неизменяем => не поддерживается.
		"""
		if type(dependency) in self._IMMUTABLE_TYPES:
			raise DependencyCannotBeImmutableType(
				f"Object '{name}' is immutable, so it can't be here. \
Use Ref() class for make his mutable. \
Immutable (unsupported) types: {', '.join({str(immutable_type) for immutable_type in self._IMMUTABLE_TYPES})}"
			)

	def __init__(self, **dependencies):
		for name, dependency in dependencies.items():
			self.__check_dependency_object_type_mutable(name, dependency)
		
		dependencies['this_dependency_container'] = self
		self._dependencies: Dict[str, Any] = dependencies

		assert self.get('this_dependency_container') is self

	def __len__(self) -> int:
		return len(self._dependencies)
	
	def __contains__(self, dependency: Any | str) -> bool:
		if isinstance(dependency, str):
			return dependency in self._dependencies
		else:
			return dependency in self._dependencies.values()
	
	def __copy__(self) -> Self:
		new_deps = DependencyContainer(
			**self._dependencies
		)
		assert new_deps.get('this_dependency_container') is new_deps

		return new_deps
	
	def __str__(self) -> str:
		return str(self._dependencies)
	

	def add(self, **new_dependencies):
		"""
		Добавляет зависимости в контейнер. В качестве значения необходимо указывать ссылку, а не значение.

		:raise KeyError: Одна или несколько зависимостей с таким именем уже есть
		"""

		conflict_dependencies:  List[str] = []
		dependencies_to_adding: Dict[str, Any] = {}

		for name, new_dependency in new_dependencies.items():
			self.__check_dependency_object_type_mutable(name, new_dependency)

			if name in self:
				conflict_dependencies.append(name)
				continue

			dependencies_to_adding[name] = new_dependency
		
		if conflict_dependencies:
			raise KeyError(
				f"Dependency '{conflict_dependencies[0]}' is already in the DependencyContainer" if len(conflict_dependencies) == 1
				else f"The dependencies {', '.join(conflict_dependencies)} already in the DependencyContainer."
			)

		self._dependencies.update(dependencies_to_adding)
		
	'''
	def remove(self, name: str):
		"""
		Удаляет зависимость

		:raise KeyError: Зависимости не существует
		"""

		if name not in self._dependencies:
			raise KeyError(f"Dependency '{name}' does not exist")
		
		del self._dependencies[name]
	'''

	def get(self, name: str) -> Any | None:
		"""Возвращает зависимость по имени. Вернёт `None`, если такой зависимости нет."""

		return self._dependencies.get(name.strip())
	

	def resolve(
			self,
			customer: Callable
		):
		"""
		Возвращает словарь с зависимостями, необходимыми для выполнения функции, если таковые есть.
		Если каких-то зависимостей нет - вызовет ошибку, в которой укажет каких именно зависимостей
		не хватает и какие есть на текущий момент.

		#### Пример:
		```
			# При чём здесь `Ref` - см. в docstring DependencyContainer
			def funny_func(bottles_count: Ref[int], persons: List[str])
				pass
			
			dependencies = DependencyContainer(
				bottles_count = Ref(12),
				persons = ['Oleg', 'Pavel', 'Nekitos']
			)

			funny_func(**dependencies.resolve(funny_func))
		```

		:param customer: Функция "заказчик".

		:raise MissingDependencyError: Одной или нескольких зависимостей в контейнере не хватает.
			В ошибке пропишет каких не хватает и какие есть.
		"""
		
		required_dependencies: Dict[str, Any] = dict()
		missing_dependencies:  List[str]      = list()

		for required_parameter in inspect.signature(customer).parameters:
			if required_parameter not in self:
				missing_dependencies.append(required_parameter)
				continue
				
			required_dependencies[required_parameter] = self.get(required_parameter)
			
		if missing_dependencies:
			raise MissingDependencyError(
				f"\nNecessary dependencies are missing: {', '.join(sorted(missing_dependencies))}.\n" +
				f"Available dependencies: {', '.join(sorted(self._dependencies))}"
			)

		return required_dependencies
	
async def resolve_and_call(
		func: Callable[..., Any] | Callable[..., Awaitable[Any]],
		dependencies: DependencyContainer
	):

	"""
	Вызывает функцию и решает её зависимости. Работает как с синхронными, так и с асинхронными функциями.

	#### Пример:
	```
	# Sync
	result = resolve_and_call(sync_func, dependencies)

	# Async
	result = await resolve_and_call(async_func, dependencies)
	```

	:param func: Функция (синхронная / асинхронная)
	:param dependencies: Контейнер с зависимостями.

	:return: Результат выполнения функции или корутину с результатом (или как оно там).
	"""

	required_dependencies: Dict[str, Any] = dependencies.resolve(func)

	if inspect.iscoroutinefunction(func):
		return await func(**required_dependencies)
	
	else:
		return func(**required_dependencies)