# main.py
import datetime
import json

import os
from flask import Blueprint, render_template, request, send_from_directory, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from project.forms import UploadForm
from .models import User, UploadedContent
from . import db, app, ALLOWED_EXTENSIONS
from flask import url_for, redirect


# main = Blueprint('main', __name__)


@app.route('/', methods=['GET', 'POST'])
@login_required
def profile():
    if request.form:
        first_name = request.form.get('first_name', current_user.first_name)
        last_name = request.form.get('last_name', current_user.last_name)
        email = request.form.get('email', current_user.email)
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.email = email
        db.session.commit()
        return redirect('/profile')

    return render_template('profile.html', user=current_user)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload_file', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_file',
                                    filename=filename))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''


@app.route('/upload/content', methods=['GET', 'POST'])
def upload_content():
    form = UploadForm()
    if request.method == 'POST':
        if form.validate():
            file = request.files['content']
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            upload_content = UploadedContent(user=current_user.id, from_date=form.from_date.data,
                                             to_date=form.to_date.data,
                                             content=filename, linie=form.linie.data or 0)
            db.session.add(upload_content)
            db.session.commit()
            flash('Content Uploaded Successfully')

    return render_template('upload_content.html', form=form)
