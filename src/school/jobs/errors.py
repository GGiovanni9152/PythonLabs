class QueueFullError(Exception):
    """Очередь переполнена"""

class JobNotFoundError(Exception):
    """Задание не найдено"""