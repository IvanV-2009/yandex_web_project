from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo


class SendMessageForm(FlaskForm):
    message = TextAreaField('Сообщение', validators=[DataRequired()])
    submit = SubmitField('Отправить')
