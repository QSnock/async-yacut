import re
from flask import jsonify, request, url_for

from .app import app, db
from .models import URLMap
from .utils import get_unique_short_id


def validate_custom_id(custom_id):
    """Проверяет, что custom_id содержит только латинские буквы и цифры."""
    if not custom_id:
        return True
    if len(custom_id) > 16:
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
        return None, jsonify({'message': 'Отсутствует тело запроса'}), 400

    data = request.get_json(silent=True)
    if data is None:
        return None, jsonify({'message': 'Отсутствует тело запроса'}), 400

    url = data.get('url')
    if not url:
        return None, jsonify(
            {'message': '"url" является обязательным полем!'}
        ), 400

    custom_id = data.get('custom_id')
    if custom_id:
        custom_id = custom_id.strip()
    if not custom_id:
        custom_id = None

    return (url, custom_id), None, None


def get_short_id(custom_id):
    """Получает short_id, проверяя custom_id если он указан."""
    if not custom_id:
        return get_unique_short_id(), None, None

    if not validate_custom_id(custom_id):
        return None, jsonify(
            {'message': 'Указано недопустимое имя для короткой ссылки'}
        ), 400

    existing = URLMap.query.filter_by(short=custom_id).first()
    if existing:
        return None, jsonify(
            {
                'message': 'Предложенный вариант короткой '
                           'ссылки уже существует.'
            }
        ), 400

    return custom_id, None, None


@app.route('/api/id/', methods=['POST'])
def create_id():
    """Создание короткой ссылки через API."""
    request_data, error_response, error_code = validate_request()
    if error_response:
        return error_response, error_code

    url, custom_id = request_data

    short_id, error_response, error_code = get_short_id(custom_id)
    if error_response:
        return error_response, error_code

    try:
        save_url_map(url, short_id)
    except Exception:
        db.session.rollback()
        if custom_id:
            return jsonify(
                {
                    'message': 'Предложенный вариант короткой '
                               'ссылки уже существует.'
                }
            ), 400
        short_id = get_unique_short_id()
        save_url_map(url, short_id)

    short_link = url_for('redirect_view', short_id=short_id, _external=True)
    return jsonify({
        'url': url,
        'short_link': short_link
    }), 201


@app.route('/api/id/<short_id>/', methods=['GET'])
def get_url(short_id):
    """Получение оригинальной ссылки по короткому идентификатору."""
    url_map = URLMap.query.filter_by(short=short_id).first()
    if not url_map:
        return jsonify({'message': 'Указанный id не найден'}), 404

    return jsonify({'url': url_map.original}), 200
