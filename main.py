#!/usr/bin/python
import zlib
from urllib import parse
from asyncmc import Client
from http import cookiejar
from lxml import html as ht
from http import client, cookies
import logging
import tornado.ioloop
import tornado.httpclient
import os

class Uploader(object):
    upload_to = 'upload_img'
    def __init__(self):
        if not os.path.exists(self.upload_to):
            os.makedirs(self.upload_to)

    def upload(self, response, file_name):
        file_name = os.path.join(self.upload_to,file_name) 
        with open(file_name, "wb") as f:
            f.write(response)
        return file_name

class Connector(object):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Connection': 'keep-alive',
        'Host': 'www.secure.pixiv.net',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4,es;q=0.2,sq;q=0.2',
        'Accept-Encoding': 'gzip,deflate,sdch',
        }

    def __init__(self, *ar, **kw):
        self.cache = Client()
        logging.info('init call')
        self.cache.get('pixv_session', self.call_session)
        self.server = tornado.ioloop.IOLoop.instance()
        self.block()
        self.uploader = Uploader()
        self.d = zlib.decompressobj(16+zlib.MAX_WBITS)

    def block(self, *ar, **kw):
        self.server.start()

    def unblock(self, *ar, **kw):
        self.server.stop()

    def get_ranking(self):
        url = 'www.pixiv.net'
        self.conn = client.HTTPConnection(url, timeout=60)
        self.conn.request('GET', '/ranking.php?mode=daily', headers = self.headers)
        resp = self.conn.getresponse()
        self.set_cookie(resp)
        html = ht.fromstring(self.d.decompress(resp.read()))
        logging.info(self.headers)
        count = []

        def image_upload(resp):
            count.pop()
            self.uploader.upload(resp.body, resp.request.url.split('/')[-1])
            if not len(count):
                self.unblock()

        self.headers.update({
            'Host': 'i2.pixiv.net',
            })
        async_client = tornado.httpclient.AsyncHTTPClient()
        for it in html.xpath("//*[contains(@class,'ranking-item')]")[:5]:
            count.append('')
            url = it.xpath('.//img')[0].get('data-src')
            request = tornado.httpclient.HTTPRequest(url, headers=self.headers)
            async_client.fetch(request, image_upload)
            logging.info(url)

        self.block()

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

    def call_session(self, rez):
        logging.info('in session {}'.format(rez))
        if rez:
            self.headers = rez
            self.unblock()
            return
        url = 'www.secure.pixiv.net'
        conn = client.HTTPSConnection(url, timeout=60)
        conn.request('GET', '/login.php', headers = self.headers)
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
            'pixiv_id': 'anon',
            'pass': 'anon',
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
            logging.info('set_cache')
            self.cache.set('pixv_session', self.headers, 1000, self.unblock)
        else:
            logging.error('login error')

def parser():
    connection = Connector()
    connection.get_ranking()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    parser()

