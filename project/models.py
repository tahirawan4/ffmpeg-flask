# models.py

from flask_login import UserMixin
from . import db
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    first_name = db.Column(db.String(1000))
    last_name = db.Column(db.String(1000))


class UploadedContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    from_date = db.Column(db.Date)
    to_date = db.Column(db.Date)
    linie = db.Column(db.INTEGER)
    content = db.Column(db.String(200))
    user = db.Column(db.Integer, db.ForeignKey('user.id'))


# class Quote(db.Model):
#     id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
#     title = db.Column(db.String(100))
#     description = db.Column(db.String(1000))
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
#     date_added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
#
#     @hybrid_property
#     def user_first_name(self):
#         return User.query.filter_by(id=self.user_id).first().first_name
#
#     @hybrid_property
#     def total_likes(self):
#         return len(QuoteLike.query.filter_by(quote_id=self.id).all())
#
#     @hybrid_method
#     def can_like(self, user_id):
#         return False if QuoteLike.query.filter_by(quote_id=self.id, user_id=user_id).first() else True
#
#     @hybrid_method
#     def can_edit(self, user_id):
#         return True if user_id == self.user_id else False
#
#
# class QuoteLike(db.Model):
#     id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
#     quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'))
