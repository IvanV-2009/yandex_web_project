import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin
from sqlalchemy import orm

subscriptions = sqlalchemy.Table('subscriptions',
                                 SqlAlchemyBase.metadata,
                                 sqlalchemy.Column('follower_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'),
                                                   primary_key=True),
                                 sqlalchemy.Column('followed_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'),
                                                   primary_key=True)
                                 )


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    about = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String,
                              index=True, unique=True, nullable=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)

    followed = orm.relationship(
        'User',
        secondary=subscriptions,
        primaryjoin=(subscriptions.c.follower_id == id),
        secondaryjoin=(subscriptions.c.followed_id == id),
        backref='followers',
        lazy='dynamic'
    )

    liked_posts = orm.relationship('Like', backref='users', lazy='dynamic')

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def follow(self, user):
        if user != self and not self.is_following(user):
            self.followed.append(user)
            return self

    def is_following(self, user):
        return self.followed.filter(
            subscriptions.c.followed_id == user.id
        ).count() > 0

    def unfollow(self, user):
        if user != self and self.is_following(user):
            self.followed.remove(user)
            return self

