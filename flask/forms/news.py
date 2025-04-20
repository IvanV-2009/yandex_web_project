from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired
from wtforms import FileField
from flask_wtf.file import FileAllowed, FileRequired


class NewsForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    content = TextAreaField("Содержание")
    is_private = BooleanField("Личное")
    image = FileField('Изображение статьи', validators=[
             FileAllowed(['jpg', 'png'], 'Только изображения!')
         ])
    tags = StringField('Теги (через запятую)')
    submit = SubmitField('Применить')