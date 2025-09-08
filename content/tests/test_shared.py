import content.shared.messages as shared

# MARK: TEST MessageType
def test_message_type_consistency():
	for msg_type in shared.MessageType:
		name: str = msg_type.name.lower().replace('.','_')
		value: str = msg_type.value

		assert value == name, f"Inconsistent name and value in MessageType: {value} != {name}"