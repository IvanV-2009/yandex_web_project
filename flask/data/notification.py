import datetime
import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Notification(SqlAlchemyBase):
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('user.id'))
    message = sqlalchemy.Column(sqlalchemy.String(200))
    is_read = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
