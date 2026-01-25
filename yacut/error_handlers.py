from flask import render_template

from .app import app, db


@app.errorhandler(404)
def page_not_found(error):
    """Обработчик ошибки 404 для UI."""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Обработчик внутренней ошибки сервера."""
    db.session.rollback()
    return render_template('404.html'), 500
