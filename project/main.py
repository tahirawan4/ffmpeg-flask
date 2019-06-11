# main.py
import datetime
import json
import threading

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

VIDEO = 'Video'
IMAGE = 'Image'


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


def file_type_allowed(upload_file_type):
    for file_type in ALLOWED_EXTENSIONS:
        if file_type in upload_file_type:
            return True
    return False


@app.route('/upload/content', methods=['GET', 'POST'])
@login_required
def upload_content():
    form = UploadForm()
    if current_user.get_user_role() == 'admin':
        data_instances = DataInstance.query.all()
    else:
        data_instances = current_user.data_instances

    if request.method == 'POST':
        if form.validate():
            import magic
            file = request.files['content']
            filename = secure_filename(file.filename)
            file.save(os.path.join('/tmp', filename))
            file_type = magic.from_file(os.path.join('/tmp', secure_filename(file.filename)))

            if file_type_allowed(file_type):
                file_type = VIDEO if 'mp4' in file_type.lower() else IMAGE
                second_filename = '{}_{}'.format(datetime.datetime.now().strftime("%y%m%d_%H%M%S"),
                                                 secure_filename(file.filename))
                upload_content = UploadedContent(user=current_user.id, from_date=form.from_date.data,
                                                 to_date=form.to_date.data,
                                                 content=second_filename, linie=form.linie.data or 0,
                                                 file_type=file_type, duration=form.duration.data or 0,
                                                 data_instance=form.data_instance.data, status='Processing',
                                                 coordinates=form.coordinates.data)

                db.session.add(upload_content)
                db.session.commit()

                data_instance = DataInstance.query.filter_by(id=upload_content.data_instance).first()

                convert_video(filename, second_filename,
                              data_instance.ffmpeg_params if file_type == VIDEO else data_instance.ffmpeg_params_image,
                              upload_content.id)
                flash('Content Uploaded Successfully')
                return redirect(url_for('uploaded_contents'))
            else:
                flash('File type not supported.')

    return render_template('upload_content.html', form=form, data_instances=data_instances, upload_content=None)


@app.route('/edit/<int:id>/upload/content', methods=['GET', 'POST'])
@login_required
def edid_upload_content(id):
    form = UploadForm()
    upload_content = UploadedContent.query.filter_by(id=id).first()
    if current_user.get_user_role() == 'admin':
        data_instances = DataInstance.query.all()
    else:
        data_instances = current_user.data_instances
    if request.method == 'POST':
        if form.validate():
            upload_content.from_date = form.from_date.data
            upload_content.to_date = form.to_date.data
            upload_content.linie = form.linie.data
            upload_content.duration = form.duration.data
            upload_content.data_instance = form.data_instance.data
            upload_content.coordinates = form.coordinates.data
            db.session.commit()
            flash('Content Updated Successfully')
            return redirect(url_for('uploaded_contents'))

    return render_template('upload_content.html', form=form, data_instances=data_instances,
                           upload_content=upload_content)


@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if current_user.get_user_role() != 'admin':
        return redirect(url_for('data_instances'))
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
    if current_user.get_user_role() != 'admin':
        return redirect(url_for('data_instances'))
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
    if current_user.get_user_role() != 'admin':
        return redirect(url_for('data_instances'))
    user = User.query.filter_by(id=id).first()
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('platform_users'))


@app.route('/delete_instance/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_instance(id):
    instance = UploadedContent.query.filter_by(id=id).first()
    try:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], instance.content))
    except:
        pass
    db.session.delete(instance)
    db.session.commit()
    return redirect(url_for('uploaded_contents'))


@app.route('/platform_users', methods=['GET', 'POST'])
@login_required
def platform_users():
    if current_user.get_user_role() != 'admin':
        return redirect(url_for('data_instances'))
    users = User.query.all()
    data_instances = DataInstance.query.all()
    return render_template('platform_users.html', platform_users='active', users=users, data_instances=data_instances)


@app.route('/uploaded_contents', methods=['GET', 'POST'])
@login_required
def uploaded_contents():
    if current_user.get_user_role() == 'admin':
        data_instances = UploadedContent.query.all()
    else:
        data_instances = current_user.data_instances
        data = []
        for instance in data_instances:
            data.extend(UploadedContent.query.filter_by(data_instance=instance.id))
        data_instances = data

    return render_template('uploaded_contents.html', uploaded_contents='active', data_instances=data_instances)


#
# def popenAndCall(onExit, *popenArgs, **popenKWArgs):
#     """
#     Runs a subprocess.Popen, and then calls the function onExit when the
#     subprocess completes.
#
#     Use it exactly the way you'd normally use subprocess.Popen, except include a
#     callable to execute as the first argument. onExit is a callable object, and
#     *popenArgs and **popenKWArgs are simply passed up to subprocess.Popen.
#     """
#     def runInThread(onExit, popenArgs, popenKWArgs):
#         proc = subprocess.Popen(*popenArgs, **popenKWArgs)
#         proc.wait()
#         onExit()
#         return
#
#     thread = threading.Thread(target=runInThread,
#                               args=(onExit, popenArgs, popenKWArgs))
#     thread.start()
#
#     return thread # returns immediately after the thread starts
#



def runInThread(content_id, popenArgs, popenKWArgs):
    proc = subprocess.Popen(popenArgs)
    proc.wait()
    # uploaded = UploadedContent.query.filter_by(id=content_id).first()
    # uploaded.status = "Processed"
    # db.session.commit()
    return


def convert_video(video_input, video_output, ffmpeg_params, content_id):
    cmds = ['ffmpeg', '-i', os.path.join('/tmp', video_input)]
    cmds.extend(ffmpeg_params.split(' '))
    cmds.extend([os.path.join(app.config['UPLOAD_FOLDER'], video_output)])

    thread = threading.Thread(target=runInThread, args=(content_id, cmds, None))
    thread.start()


@app.route('/playlist', methods=['GET'])
@login_required
def playlist():
    now = datetime.datetime.now().date()
    if current_user.get_user_role() == 'admin':
        data_instances = UploadedContent.query.filter(db.func.date(UploadedContent.from_date) <= now,
                                                      db.func.date(UploadedContent.to_date) >= now).all()

    else:
        data_instances = current_user.data_instances
        data = []
        for instance in data_instances:
            data.extend(UploadedContent.query.filter(db.func.date(UploadedContent.from_date) <= now,
                                                     db.func.date(UploadedContent.to_date) >= now,
                                                     UploadedContent.data_instance == instance.id).all())
        data_instances = data

    data = []
    for instance in data_instances:
        data.append({
            "type": str(instance.file_type).lower(),
            "linie": str(instance.linie),
            "duration": str(instance.duration),
            "date_from": instance.from_date.strftime("%m.%d.%Y"),
            "date_to": instance.to_date.strftime("%m.%d.%Y"),
            "filename": "{}{}/{}".format(request.url_root, 'uploads', instance.content)
        })

    return jsonify(data)


@app.route('/all_data_instances', methods=['GET', 'POST'])
@login_required
def data_instances():
    if current_user.get_user_role() == 'admin':
        data_instances = DataInstance.query.all()
    else:
        data_instances = current_user.data_instances

    return render_template('data_instances.html', data_instance='active', data_instances=data_instances)


@app.route('/add-data-instance', methods=['GET', 'POST'])
@login_required
def add_data_instabce_new():
    if current_user.get_user_role() != 'admin':
        return redirect(url_for('data_instances'))
    if request.form:
        data_type = request.form.get('data_type')
        scale_param = request.form.get('scale_param')
        name = request.form.get('name')
        description = request.form.get('description')
        ffmpeg_params = request.form.get('ffmpeg_params')
        ffmpeg_params_image = request.form.get('ffmpeg_params_image')

        data_instance = DataInstance(data_type=data_type, scale_param=scale_param, name=name, description=description,
                                     ffmpeg_params=ffmpeg_params, ffmpeg_params_image=ffmpeg_params_image)

        db.session.add(data_instance)
        db.session.commit()

        return redirect(url_for('data_instances'))

    return render_template('add_data_instance.html', add_user='active', user=None)


@app.route('/edit-data-instance/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_data_instabce_new(id):
    if current_user.get_user_role() != 'admin':
        return redirect(url_for('data_instances'))
    data_instance = DataInstance.query.filter_by(id=id).first()
    if request.form:
        data_type = request.form.get('data_type')
        scale_param = request.form.get('scale_param')
        name = request.form.get('name')
        description = request.form.get('description')
        ffmpeg_params = request.form.get('ffmpeg_params')
        ffmpeg_params_image = request.form.get('ffmpeg_params_image')

        data_instance.data_type = data_type or data_instance.data_type
        data_instance.scale_param = scale_param or data_instance.scale_param
        data_instance.name = name or data_instance.name
        data_instance.description = description or data_instance.description
        data_instance.ffmpeg_params = ffmpeg_params or data_instance.ffmpeg_params
        data_instance.ffmpeg_params_image = ffmpeg_params_image or data_instance.ffmpeg_params_image

        db.session.commit()

        return redirect(url_for('data_instances'))

    return render_template('add_data_instance.html', add_user='active', data_instance=data_instance)


@app.route('/delete_data_instance/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_data_instance(id):
    if current_user.get_user_role() != 'admin':
        return redirect(url_for('data_instances'))
    data = DataInstance.query.filter_by(id=id).first()
    db.session.delete(data)
    db.session.commit()
    return redirect(url_for('data_instances'))


@app.route('/link_data_instance/<int:id>', methods=['POST'])
@login_required
def link_user_instance(id):
    if current_user.get_user_role() != 'admin':
        return redirect(url_for('data_instances'))
    user = User.query.filter_by(id=id).first()
    instances = request.form.getlist('instances[]')
    user.data_instances = []
    db.session.commit()
    for instance_id in instances:
        data_inst = DataInstance.query.filter_by(id=instance_id).first()
        user.data_instances.append(data_inst)
    db.session.commit()
    return redirect(url_for('platform_users'))
