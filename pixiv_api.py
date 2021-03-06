#!/usr/bin/python
import zlib, collections
import functools
from uuid import uuid4

from urllib import parse
from asyncmc import Client
from http import cookiejar
from lxml import html as ht
from http import client, cookies
import logging
import tornado.ioloop
import tornado.httpclient
from tornado import gen
import os
from tornado.concurrent import Future


class Uploader(object):
    upload_to = 'nginx/media/upload_img'
    tested_urls = collections.defaultdict(str)
    
    def __init__(self, url_fn):
        self.url_fn = url_fn
        if not os.path.exists(self.upload_to):
            os.makedirs(self.upload_to)

    def url_test(self, url):
        file_name = self.url_fn(url)
        file_name = os.path.join(self.upload_to, file_name) 
        if not os.path.exists(file_name):
            self.tested_urls[url] = file_name
            file_name = False
        return file_name

    def upload(self, response, file_name):
        logging.info('load')
        file_name = self.tested_urls[file_name]
        if file_name:
            dir_name = os.path.dirname(file_name)
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
            with open(file_name, "wb") as f:
                f.write(response)
        return '/'+file_name

class Connector(object):

    class LoginError(Exception):

        def __init__(self, info):
            self.info = info

        def __str__(self):
            return repr(self.info)

    def __init__(self,  *ars, **kw):
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Host': 'www.secure.pixiv.net',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4,es;q=0.2,sq;q=0.2',
            'Accept-Encoding': 'gzip,deflate,sdch',
            }
        self.errors = {}
        self.cache = Client(servers=['memcached:11211'])
        self.id = kw.get('id', uuid4().hex)

        self.server = tornado.ioloop.IOLoop.instance()
        self.uploader = Uploader(url_fn=self.url_to_name)
        self.d = zlib.decompressobj(16+zlib.MAX_WBITS)

    def url_to_name(self, url):
        return url.split('//')[1].replace('.pixiv.net', '')

    def login_fut(self):
        return self.cache.get(self.id)

    def get_login_fut(self, login='', password=''):
        fut = Future()
        get_fut = self.login_fut()
        def wraper(fut_rez):
            info = fut_rez.result()
            info = self.call_session(info, login, password)
            fut.set_result(info)
        get_fut.add_done_callback(wraper)
        return fut
        
    def call_session(self, rez, login='', password=''):
        if rez:
            self.headers = rez
            self.unblock()
            self.cache.set(self.id, self.headers, 1000)
            return False
        elif not login:
            raise self.LoginError('login is none')
        url = 'www.secure.pixiv.net'
        conn = client.HTTPSConnection(url, timeout=6)
        conn.request('GET', '/login.php', headers = self.headers)
        logging.info('get resp')
        response = conn.getresponse()
        self.set_cookie(response)
        self.headers.update({
            'Origin': 'https://www.secure.pixiv.net',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://www.secure.pixiv.net/login.php',
            'Cache-Control': 'max-age=0'
            })
        response.read()
        info = {
            'pixiv_id': login,
            'pass': password,
            'mode': 'login',
            'skip': '1',
        }
        data = parse.urlencode(info).encode('utf-8')
        conn.request('POST', '/login.php', body=data, headers=self.headers)
        response = conn.getresponse()
        self.set_cookie(response)
        for k in ['Origin', 'Content-Type', 'Referer']:
            self.headers.pop(k) 
        self.headers.update({
            'Host': 'www.pixiv.net',
            })
        conn.close()
        if response.status == 302:
            self.cache.set(self.id, self.headers, 1000)
            return False
        else:
            return {'login': 'pixiv login error'}

    def block(self, *ar, **kw):
        logging.info('block call')

    def unblock(self, *ar, **kw):
        logging.info('unblock call {}'.format(ar))

    def get_ranking(self):
        url = 'www.pixiv.net'
        fut = Future()
        count = []
        out_info = {
                'images': [],
                }

        async_client = tornado.httpclient.AsyncHTTPClient()

        def image_upload(resp, description_info={}):
            count.pop()
            local_file_name = self.uploader.upload(resp.body, resp.request.url)
            description_info.update({
                'local': local_file_name,
                'url': resp.request.url,
                })
            out_info['images'].append(description_info)

            if not len(count):
                fut.set_result(out_info)
                self.unblock()

        def info_upload(resp):
            html = ht.fromstring(resp.body)
            self.headers.update({
                'Host': 'i2.pixiv.net',
                })
            for it in html.xpath(
                    "//section[contains(@class,'ranking-item')]")[:9]:
                url = it.xpath('.//img')[0].get('data-src')
                description_info = {
                    'name': it.xpath('.//h2/a')[0].text
                    }

                file_name = self.uploader.url_test(url)
                if not file_name:
                    count.append('')
                    request = tornado.httpclient.HTTPRequest(url, headers=self.headers)
                    def decor(resp):
                        image_upload(resp, description_info)
                    async_client.fetch(request, decor)
                else:
                    description_info.update({
                        'local': file_name,
                        'url': url,
                        })
                    out_info['images'].append(description_info)

            if not len(count):
                fut.set_result(out_info)
                self.unblock()

        request = tornado.httpclient.HTTPRequest('http://{}{}'.format(
            url, '/ranking.php?mode=daily'),
            headers=self.headers, connect_timeout=60)
        async_client.fetch(request, info_upload)

        return fut

    def set_cookie(self, response):
        C = cookies.SimpleCookie()
        cookies_dict = {}
        if self.headers.get('Cookie'):
            cookies_dict = dict(([(lambda i: (i[0], i[1]))(raw.split('=')) \
                    for raw in self.headers['Cookie'].split('; ')]))
        cookies_dict['visit_ever'] = 'yes'
        for k, v in response.getheaders():
            if k == 'Set-Cookie':
                C.load(v)
        for k, v in  C.items():
            cookies_dict[k] = v.value
        self.headers['Cookie'] = '; '.join(['{}={}'.format(k,v) for k, v in cookies_dict.items()])

    def add_err(self, msg):
        logging.error(msg)
        self.unblock()
        self.errors.update(msg)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    connection = Connector(login = "txest", password = "test")
    #connection.get_ranking()
