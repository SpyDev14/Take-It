from shared import INVALID_CHARACTERS, is_valid_name

name: str = input('Name: ')
if name.isspace() or len(name) == 0:
    print('Invalid input')
    exit()
    
print(f'{name} is {'valid name' if is_valid_name(name) else 'wrong name'}')