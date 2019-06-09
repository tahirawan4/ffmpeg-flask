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
