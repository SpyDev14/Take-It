class MissingDepencyError(ValueError):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

class ImmutableDependencyTypeError(TypeError):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)