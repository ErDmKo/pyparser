import json

import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.web

from tornado import gen
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
            login_url="/server/auth/login",
        )
        tornado.web.Application.__init__(self, handlers, **settings)


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user_json = self.get_secure_cookie("authdemo_user")
        if not user_json: return None
        return tornado.escape.json_decode(user_json)

class AuthHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        form = forms.LoginForm(self.request.arguments)
        if form.validate():
            self.write(json.dumps(form.data))
        else:
            self.write(json.dumps(form.errors))

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("authdemo_user")
        self.write('You are now logged out. '
                   'Click <a href="/">here</a> to log back in.')
def main():
    parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
