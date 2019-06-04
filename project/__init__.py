# init.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from os.path import join, dirname, realpath
from flask_migrate import Migrate

# init SQLAlchemy so we can use it later in our models
db = SQLAlchemy()
UPLOAD_FOLDER = join(dirname(realpath(__file__)), 'media/')
# ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'mp4'])
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
# def create_app():
app = Flask(__name__)
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
