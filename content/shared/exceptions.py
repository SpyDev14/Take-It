class MissingDependencyError(ValueError):
	def __init__(self, *args):
		super().__init__(*args)

class DependencyCannotBeImmutableType(TypeError):
	def __init__(self, *args):
		super().__init__(*args)