from wtforms import Form, BooleanField, StringField, PasswordField, validators, IntegerField, FileField, \
    SubmitField, DateField

from flask_wtf import FlaskForm


class UploadForm(FlaskForm):
    from_date = DateField('From Date', [validators.DataRequired()])
    to_date = DateField('To Date', [validators.DataRequired()])
    linie = IntegerField()
    content = FileField('Content')

    submit = SubmitField('Submit')
    # username = StringField('Username', [validators.Length(min=3, max=25)])
    # email = StringField('Email Address', [validators.Length(min=6, max=35)])
    # password = PasswordField('New Password', [
    #     validators.DataRequired(),
    #     validators.EqualTo('confirm', message='Passwords must match')
    # ])
    # confirm = PasswordField('Repeat Password')
    # accept_tos = BooleanField('I accept the TOS', [validators.DataRequired()])
