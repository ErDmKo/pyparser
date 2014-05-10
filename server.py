import json, logging

import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.web

from tornado import gen, autoreload
from tornado.options import define, options, parse_command_line

import forms

define("port", default=8000, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/server/auth/login", AuthHandler),
            (r"/server/auth/logout", LogoutHandler),
        ]
        settings = dict(
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            login_url="/",
        )
        tornado.web.Application.__init__(self, handlers, **settings)


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user_json = self.get_secure_cookie("auth_id")
        if not user_json: return None
        return tornado.escape.json_decode(user_json)

class AuthHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        name = tornado.escape.xhtml_escape(self.current_user['login'])
        self.write("Hello, " + name)
        self.write("<br><br><a href=\"/server/auth/logout\">Log out</a>")

    @gen.coroutine
    def post(self):
        data = json.loads(self.request.body.decode('utf8'))
        form = forms.LoginForm(forms.TornadoMultiDict(data))
        logging.info(data)
        if form.validate():
            self.set_secure_cookie("auth_id", tornado.escape.json_encode({'login': form.data['login']}))
            self.write(form.data)
        else:
            self.set_status(401)
            self.write(form.errors)

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("auth_id")
        self.write('You are now logged out. '
                   'Click <a href="/">here</a> to log back in.')

def main():
    parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    ioloop = tornado.ioloop.IOLoop().instance()
    autoreload.start(ioloop)
    ioloop.start()

if __name__ == "__main__":
    main()
