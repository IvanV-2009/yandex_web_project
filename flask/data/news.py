import datetime
import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase, create_session


class News(SqlAlchemyBase):
    __tablename__ = 'news'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    content = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    image_path = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)
    is_private = sqlalchemy.Column(sqlalchemy.Boolean, default=True)

    likes = orm.relationship('Like', backref='news')
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    user = orm.relationship('User')
    news_tags = orm.relationship("Tags",
                                 secondary="association",
                                 backref="news",
                                 cascade="save-update, merge",
                                 passive_deletes=True)

    def likes_count(self):
        return len(self.likes)

    def is_liked_by(self, user):
        return self.likes.filter()
