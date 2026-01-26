import re
from http import HTTPStatus

from flask import jsonify, request, url_for

from .app import app, db
from .constants import MAX_SHORT_ID_LENGTH
from .error_handlers import APIException
from .models import URLMap
from .utils import get_unique_short_id


def validate_custom_id(custom_id):
    """Проверяет, что custom_id содержит только латинские буквы и цифры."""
    if not custom_id:
        return True
    if len(custom_id) > MAX_SHORT_ID_LENGTH:
        return False
    if not re.match(r'^[a-zA-Z0-9]+$', custom_id):
        return False
    return True


def save_url_map(url, short_id):
    """Сохраняет URLMap в бд."""
    url_map = URLMap(original=url, short=short_id)
    db.session.add(url_map)
    db.session.commit()


def validate_request():
    """Проверяет запрос и извлекает данные."""
    if not request.is_json:
        raise APIException(
            'Отсутствует тело запроса', HTTPStatus.BAD_REQUEST
        )

    data = request.get_json(silent=True)
    if data is None:
        raise APIException(
            'Отсутствует тело запроса', HTTPStatus.BAD_REQUEST
        )

    url = data.get('url')
    if not url:
        raise APIException(
            '"url" является обязательным полем!',
            HTTPStatus.BAD_REQUEST
        )

    custom_id = data.get('custom_id')
    if custom_id:
        custom_id = custom_id.strip()
    if not custom_id:
        custom_id = None

    return url, custom_id


def get_short_id(custom_id):
    """Получает short_id, проверяя custom_id если он указан."""
    if not custom_id:
        return get_unique_short_id()

    if not validate_custom_id(custom_id):
        raise APIException(
            'Указано недопустимое имя для короткой ссылки',
            HTTPStatus.BAD_REQUEST
        )

    existing = URLMap.query.filter_by(short=custom_id).first()
    if existing:
        raise APIException(
            'Предложенный вариант короткой ссылки уже существует.',
            HTTPStatus.BAD_REQUEST
        )

    return custom_id


@app.route('/api/id/', methods=['POST'])
def create_id():
    """Создание короткой ссылки через API."""
    url, custom_id = validate_request()

    short_id = get_short_id(custom_id)

    try:
        save_url_map(url, short_id)
    except Exception:
        db.session.rollback()
        if custom_id:
            raise APIException(
                'Предложенный вариант короткой ссылки уже существует.',
                HTTPStatus.BAD_REQUEST
            )
        short_id = get_unique_short_id()
        save_url_map(url, short_id)

    short_link = url_for('redirect_view', short_id=short_id, _external=True)
    return jsonify({
        'url': url,
        'short_link': short_link
    }), HTTPStatus.CREATED


@app.route('/api/id/<short_id>/', methods=['GET'])
def get_url(short_id):
    """Получение оригинальной ссылки по короткому идентификатору."""
    url_map = URLMap.query.filter_by(short=short_id).first()
    if not url_map:
        raise APIException('Указанный id не найден', HTTPStatus.NOT_FOUND)

    return jsonify({'url': url_map.original}), HTTPStatus.OK
