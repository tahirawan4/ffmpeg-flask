# init.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from os.path import join, dirname, realpath
from flask_migrate import Migrate
from sqlalchemy import MetaData

naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))

# init SQLAlchemy so we can use it later in our models
UPLOAD_FOLDER = join(dirname(realpath(__file__)), 'media/')
# ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'mp4'])
ALLOWED_EXTENSIONS = set(['jpg', 'jpeg','JPG', 'JPEG','MP4','mp4'])
# def create_app():
app = Flask(__name__, static_url_path='/static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SECRET_KEY'] = '9OLWxND4o83j4K4iuopO'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, '../db.sqlite')



db.init_app(app)

migrate = Migrate(app, db)
migrate.init_app(app, db, render_as_batch=True)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

from .models import User


@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return User.query.get(int(user_id))


# blueprint for auth routes in our app
from project import auth
# app.register_blueprint(auth_blueprint)

# blueprint for non-auth parts of app
from project import main
# app.register_blueprint(main_blueprint)

# return app
