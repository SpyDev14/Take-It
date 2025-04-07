import shared, os

# MARK: TEST MessageType
def test_message_type_consistency():
	for msg_type in shared.MessageType:
		name: str = msg_type.name.lower()
		value: str = msg_type.value

	assert value == name, f"Inconsistent name and value in MessageType: {value} != {name}"


if __name__ == '__main__':
	os.system('cd app')
	os.system('pytest test_shared.py')