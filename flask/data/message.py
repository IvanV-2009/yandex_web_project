# from datetime import datetime
# import sqlalchemy
# from sqlalchemy import orm
#
# from .db_session import SqlAlchemyBase, create_session
#
#
# class Message(SqlAlchemyBase):
#     __tablename__ = 'message'
#
#     id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
#     content = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
#     timestamp = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.utcnow)
#     user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('user.id'), nullable=False)
#     room_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('room.id'), nullable=False)
#     user = orm.relationship('User')
#
#     def __repr__(self):
#         return f'<Message: {self.content[:20]}...>'
