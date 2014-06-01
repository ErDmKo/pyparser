import json, logging
import functools
from asyncmc import Client
from session import MemcacheStore, Session

import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.web
import threading

from tornado import gen, autoreload
from tornado.options import define, options, parse_command_line

import forms
import pixiv_api

define("port", default=8000, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/server/auth/login", AuthHandler),
            (r"/server/auth/logout", LogoutHandler),
            (r"/server/", MainPage),
        ]
        settings = dict(
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            login_url="/",
        )
        self.session_store = MemcacheStore(Client())
        tornado.web.Application.__init__(self, handlers, **settings)


class BaseHandler(tornado.web.RequestHandler):

    @gen.coroutine
    def get_current_user(self):
        self.set_session()
        info = yield self.session.get_sessiondata()
        infos = self.session.insert_info(info, self)
        logging.info('\n\n\!!! {0} !!!\n\n'.format(infos))
        self.set_secure_cookie("auth_id", self.session._sessionid)
        return self.session['user'] if self.session and 'user' in self.session else None

    def set_session(self):
        sessionid = self.get_secure_cookie('auth_id')
        self.session =Session(self.application.session_store, sessionid)
        return self.session

class MainPage(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        name = tornado.escape.xhtml_escape(self.current_user['login'])
        info = ['hello', name]
        self.write(info)

class AuthHandler(BaseHandler):

    @gen.coroutine
    def post(self): 
        user = yield self.current_user
        logging.info(user)
        data = json.loads(self.request.body.decode('utf8'))
        form = forms.LoginForm(forms.TornadoMultiDict(data))
        if form.validate():
            logging.info(data)
            conn = pixiv_api.Connector()
            login_err = yield conn.get_login_fut(**form.data)
            if login_err:
                logging.info(login_err)
                self.set_status(401)
                self.write(login_err)
            else:
                self.session['con_obj'] = conn
                self.set_secure_cookie("auth_id", form.data['login'])
                self.write(form.data)
        else:
            self.set_status(401)
            self.write(form.errors)
        logging.info('return')

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
