# from datetime import datetime
# import sqlalchemy
# from sqlalchemy import orm
#
# from .db_session import SqlAlchemyBase, create_session
#
#
# class Room(SqlAlchemyBase):
#     __tablename__ = 'rooms'
#
#     id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
#     messages = orm.relationship('Message', backref='room', lazy=True)
#     users = orm.relationship('User', secondary='user_room', back_populates='rooms')
#
#     def __repr__(self):
#         return f'<Room {self.name}>'
