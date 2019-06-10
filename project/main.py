# main.py
import datetime
import json

import os
import subprocess
from flask import Blueprint, render_template, request, send_from_directory, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename

from project.forms import UploadForm
from .models import User, UploadedContent, DataInstance, Role
from . import db, app, ALLOWED_EXTENSIONS
from flask import url_for, redirect


# main = Blueprint('main', __name__)

@app.route('/<path:path>')
def static_file(path):
    return app.send_static_file(path)


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

    return render_template('profile.html', user=current_user, profile='active')


@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload_file', methods=['GET', 'POST'])
@login_required
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
@login_required
def upload_content():
    form = UploadForm()
    data_instances = DataInstance.query.all()
    if request.method == 'POST':
        if form.validate():
            import magic
            file = request.files['content']
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            file_type = magic.from_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            second_filename = '{}_{}'.format(datetime.datetime.now().strftime("%y%m%d_%H%M%S"),
                                             secure_filename(file.filename))
            upload_content = UploadedContent(user=current_user.id, from_date=form.from_date.data,
                                             to_date=form.to_date.data,
                                             content=second_filename, linie=form.linie.data or 0, file_type=file_type,
                                             data_instance=form.data_instance.data)
            db.session.add(upload_content)
            db.session.commit()

            convert_video(filename, second_filename)
            flash('Content Uploaded Successfully')
            return redirect(url_for('uploaded_contents'))

    return render_template('upload_content.html', form=form, data_instances=data_instances)


@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    roles = Role.query.all()
    if request.form:
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        role = request.form.get('role')
        password = request.form.get('password')

        user = User.query.filter_by(
            email=email).first()  # if this returns a user, then the email already exists in database

        if user:  # if a user is found, we want to redirect back to signup page so user can try again
            flash('Email address already exists')
            return redirect(url_for('add_user'))

        # create new user with the form data. Hash the password so plaintext version isn't saved.
        new_user = User(email=email, first_name=first_name, last_name=last_name, role=role,
                        password=generate_password_hash(password, method='sha256'))

        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('platform_users'))

    return render_template('add_user.html', add_user='active', user=None, roles=roles)


@app.route('/edit_user/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    roles = Role.query.all()
    user = User.query.filter_by(id=id).first()
    if request.form:
        password = request.form.get('password')
        user.first_name = request.form.get('first_name') or user.first_name
        user.first_name = request.form.get('last_name') or user.last_name
        user.role = request.form.get('role') or user.role
        user.password = generate_password_hash(password, method='sha256')
        db.session.commit()
        return redirect(url_for('platform_users'))

    return render_template('add_user.html', add_user='active', user=user, roles=roles)


@app.route('/delete_user/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_user(id):
    user = User.query.filter_by(id=id).first()
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('platform_users'))


@app.route('/delete_instance/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_instance(id):
    instance = UploadedContent.query.filter_by(id=id).first()
    db.session.delete(instance)
    db.session.commit()
    return redirect(url_for('uploaded_contents'))


@app.route('/platform_users', methods=['GET', 'POST'])
@login_required
def platform_users():
    users = User.query.all()
    data_instances = DataInstance.query.all()
    return render_template('platform_users.html', platform_users='active', users=users, data_instances=data_instances)


@app.route('/uploaded_contents', methods=['GET', 'POST'])
@login_required
def uploaded_contents():
    data_instances = UploadedContent.query.all()
    return render_template('uploaded_contents.html', uploaded_contents='active', data_instances=data_instances)


def convert_video(video_input, video_output):
    print(os.path.join(app.config['UPLOAD_FOLDER'], video_input))
    cmds = ['ffmpeg', '-i', os.path.join(app.config['UPLOAD_FOLDER'], video_input),
            '-vf', 'scale=1440x900', '-vcodec', 'libx264', '-an', '-sn', '-map_metadata', '-1', '-preset', 'slower',
            '-crf', '15', '-r', '25', '-pix_fmt', 'yuv420p', '-t', '14',
            os.path.join(app.config['UPLOAD_FOLDER'], video_output)]

    subprocess.Popen(cmds)


@app.route('/playlist', methods=['GET'])
@login_required
def playlist():
    data_instances = UploadedContent.query.all()
    data = []
    for instance in data_instances:
        data.append({
            "type": str(instance.file_type),
            "Linie": str(instance.linie),
            "date_from": instance.from_date.strftime("%m.%d.%Y"),
            "to_from": instance.to_date.strftime("%m.%d.%Y"),
            "filename": "{}{}/{}".format(request.url_root, 'uploads', instance.content)
        })

    return jsonify(data)


@app.route('/all_data_instances', methods=['GET', 'POST'])
@login_required
def data_instances():
    data_instances = DataInstance.query.all()
    return render_template('data_instances.html', data_instance='active', data_instances=data_instances)


@app.route('/add-data-instance', methods=['GET', 'POST'])
@login_required
def add_data_instabce_new():
    if request.form:
        data_type = request.form.get('data_type')
        scale_param = request.form.get('scale_param')
        name = request.form.get('name')
        description = request.form.get('description')
        ffmpeg_params = request.form.get('ffmpeg_params')

        data_instance = DataInstance(data_type=data_type, scale_param=scale_param, name=name, description=description,
                                     ffmpeg_params=ffmpeg_params)

        db.session.add(data_instance)
        db.session.commit()

        return redirect(url_for('data_instances'))

    return render_template('add_data_instance.html', add_user='active', user=None)


@app.route('/edit-data-instance/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_data_instabce_new(id):
    data_instance = DataInstance.query.filter_by(id=id).first()
    if request.form:
        data_type = request.form.get('data_type')
        scale_param = request.form.get('scale_param')
        name = request.form.get('name')
        description = request.form.get('description')
        ffmpeg_params = request.form.get('ffmpeg_params')

        data_instance.data_type = data_type or data_instance.data_type
        data_instance.scale_param = scale_param or data_instance.scale_param
        data_instance.name = name or data_instance.name
        data_instance.description = description or data_instance.description
        data_instance.ffmpeg_params = ffmpeg_params or data_instance.ffmpeg_params

        db.session.commit()

        return redirect(url_for('data_instances'))

    return render_template('add_data_instance.html', add_user='active', data_instance=data_instance)


@app.route('/delete_data_instance/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_data_instance(id):
    data = DataInstance.query.filter_by(id=id).first()
    db.session.delete(data)
    db.session.commit()
    return redirect(url_for('data_instances'))


@app.route('/link_data_instance/<int:id>', methods=['POST'])
@login_required
def link_user_instance(id):
    user = User.query.filter_by(id=id).first()
    instances = request.form.getlist('instances[]')
    user.data_instances = []
    db.session.commit()
    for instance_id in instances:
        data_inst = DataInstance.query.filter_by(id=instance_id).first()
        user.data_instances.append(data_inst)
    db.session.commit()
    return redirect(url_for('platform_users'))
