from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit   = SubmitField('Login')

class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit   = SubmitField('Sign Up')

class RenameForm(FlaskForm):
    user_id  = StringField('User ID', validators=[DataRequired()])
    new_name = StringField('Neuer Username', validators=[DataRequired()])
    submit   = SubmitField('Rename')

class PasswordResetForm(FlaskForm):
    user_id  = StringField('User ID', validators=[DataRequired()])
    new_pass = PasswordField('Neues Passwort', validators=[DataRequired(), Length(min=4)])
    submit   = SubmitField('Reset PW')
