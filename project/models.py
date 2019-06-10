# models.py

from flask_login import UserMixin
from . import db
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

user_data_instances_table = db.Table('user_data_instances', db.Model.metadata,
                                     db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                                     db.Column('data_instance_id', db.Integer, db.ForeignKey('data_instance.id'))
                                     )


class Role(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)

    def __str__(self):
        return self.name


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    first_name = db.Column(db.String(1000))
    last_name = db.Column(db.String(1000))
    data_instances = db.relationship("DataInstance",
                                     secondary=user_data_instances_table)
    role = db.Column(db.Integer, db.ForeignKey('role.id'))

    def get_user_role(self):
        role = Role.query.filter_by(id=self.role).first()
        if role:
            return role.name
        return None


class UploadedContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    from_date = db.Column(db.Date)
    to_date = db.Column(db.Date)
    linie = db.Column(db.INTEGER)
    content = db.Column(db.String(200))
    user = db.Column(db.Integer, db.ForeignKey('user.id'))
    file_type = db.Column(db.String(200))
    data_instance = db.Column(db.Integer, db.ForeignKey('data_instance.id'))
    status = db.Column(db.String(200))  # Processing Or Processed
    coordinates = db.Column(db.String(500))


class DataInstance(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    name = db.Column(db.String(200))
    description = db.Column(db.String(1000))
    data_type = db.Column(db.String(200))
    scale_param = db.Column(db.String(200))
    ffmpeg_params = db.Column(db.String(1000))

    def __str__(self):
        return '{}, {}'.format(self.data_type, self.scale_param)
