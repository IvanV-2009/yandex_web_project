from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, EmailField, IntegerField
from wtforms.validators import DataRequired


class SearchForm(FlaskForm):
    content = StringField('Поиск', validators=[DataRequired()])
    submit = SubmitField('Найти')
