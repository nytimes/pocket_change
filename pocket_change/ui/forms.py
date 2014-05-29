from wtforms import Form, TextField, PasswordField, SubmitField, validators
from pocket_change.auth import Authed
from flask.ext.login import login_user


class LoginForm(Form, Authed.UserCreator('Browser')):

    name = TextField('Name', [validators.Required()])
    password = PasswordField('Password', [validators.Required()])
    submit = SubmitField('Login')

    def postprocess_user(self, user):

        login_user(user)
        return user