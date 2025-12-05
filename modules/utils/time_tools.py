# modules/utils/time_tools.py

from datetime import datetime, timedelta


def get_timestamp():
    """Возвращает текущий timestamp"""
    return datetime.now().timestamp()


def format_time(timestamp):
    """Форматирует timestamp в читаемый формат"""
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def is_recent(timestamp, minutes=5):
    """Проверяет, является ли timestamp недавним"""
    now = datetime.now().timestamp()
    diff = now - timestamp
    return diff < (minutes * 60)

