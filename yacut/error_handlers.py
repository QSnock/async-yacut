from http import HTTPStatus

from flask import jsonify, render_template

from .app import app, db


class APIException(Exception):
    """Базовый класс для исключений API."""
    def __init__(self, message, status_code=HTTPStatus.BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


@app.errorhandler(APIException)
def handle_api_exception(error):
    """Обработчик исключений API."""
    return jsonify({'message': error.message}), error.status_code


@app.errorhandler(HTTPStatus.NOT_FOUND)
def page_not_found(error):
    """Обработчик ошибки 404 для UI."""
    return render_template('404.html'), HTTPStatus.NOT_FOUND


@app.errorhandler(HTTPStatus.INTERNAL_SERVER_ERROR)
def internal_error(error):
    """Обработчик внутренней ошибки сервера."""
    db.session.rollback()
    return render_template('404.html'), HTTPStatus.INTERNAL_SERVER_ERROR
