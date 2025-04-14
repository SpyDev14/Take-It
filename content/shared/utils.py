def is_null_or_whitespace(s: str | None) -> bool:
    """
    Проверяет, является ли строка `None`, пустой или состоит только из whitespace символов.
    
    :param s: Проверяемая строка
    :return: True если строка None, пустая или содержит только пробельные символы
    """
    
    return s is None or (not s.strip())