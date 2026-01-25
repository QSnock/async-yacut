from random import choice
from string import ascii_letters, digits

from .models import URLMap


def get_unique_short_id(length=6):
    """Генерирует уникальный короткий идентификатор."""
    chars = ascii_letters + digits
    while True:
        short_id = ''.join(choice(chars) for _ in range(length))
        if not URLMap.query.filter_by(short=short_id).first():
            return short_id
