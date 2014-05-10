from wtforms import validators, fields, Form

class TornadoMultiDict(dict):
    def __init__(self, response_dict):
        self.response_dict = response_dict

    def __iter__(self):
        return iter(self.response_dict)

    def __len__(self):
        return len(self.response_dict)

    def __contains__(self, name):
        return (name in self.response_dict)

    def getlist(self, name):
        return [self.response_dict[name]]

class LoginForm(Form):
    login = fields.StringField('login', validators=[validators.length(min=2), validators.Required()])
    password = fields.StringField('password', validators=[validators.length(min=2), validators.Required()])
