import re

from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, SubmitField, URLField
from wtforms.validators import (
    DataRequired, Length, Optional, URL, ValidationError
)


def validate_custom_id(form, field):
    """Валидатор для проверки custom_id.

    Проверяет, что custom_id содержит только латинские буквы и цифры.
    """
    if field.data:
        if not re.match(r'^[a-zA-Z0-9]+$', field.data):
            raise ValidationError(
                'Указано недопустимое имя для короткой ссылки'
            )
        if len(field.data) > 16:
            raise ValidationError(
                'Указано недопустимое имя для короткой ссылки'
            )


class HomeForm(FlaskForm):
    original_link = URLField(
        'Длинная ссылка',
        validators=[
            DataRequired(message='Обязательное поле'),
            URL(message='Некорректный URL')
        ]
    )
    custom_id = StringField(
        'Ваш вариант короткой ссылки',
        validators=[
            Optional(),
            Length(max=16, message='Максимальная длина 16 символов'),
            validate_custom_id
        ]
    )
    submit = SubmitField('Создать')


class DownloadForm(FlaskForm):
    files = FileField(
        'Файлы',
        render_kw={'multiple': True}
    )
    submit = SubmitField('Загрузить')
