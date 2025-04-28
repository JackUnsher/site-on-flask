"""
Утилиты для форматирования различных значений (денежные суммы, даты и т.д.)
"""

print("Модуль app.utils.format загружен успешно!")

def format_btc(amount, precision=8):
    """
    Форматирует значение Bitcoin с заданной точностью
    
    Args:
        amount (float): Сумма в BTC
        precision (int): Количество знаков после запятой (по умолчанию 8)
        
    Returns:
        str: Отформатированная строка с суммой BTC
    """
    if amount is None:
        return "0.00000000"
    
    # Форматирование числа с заданной точностью
    formatted = f"{float(amount):.{precision}f}"
    
    # Удаляем ненужные нули в конце, но оставляем хотя бы два знака после запятой
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".") if "." in formatted else formatted
        
    # Если число целое или меньше минимальной точности, добавляем запятую и нули
    if "." not in formatted:
        formatted += ".0"
    
    # Если число имеет меньше знаков после запятой, чем требуется для отображения
    # минимального значения (например, 0.00000001), добавляем нули
    parts = formatted.split(".")
    if len(parts) > 1 and len(parts[1]) < 2:
        formatted = parts[0] + "." + parts[1].ljust(2, "0")
        
    return formatted 