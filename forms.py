from wtforms import validators
from wtforms import fields
from wtforms_tornado import Form

class LoginForm(Form):
    login = fields.StringField(validators=[validators.Required()])
    password = fields.StringField(validators=[validators.Required()])
