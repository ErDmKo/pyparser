from uuid import uuid4
import time, logging
from tornado.concurrent import Future
from tornado import gen

class MemcacheStore(object):
    def __init__(self, conn, **options):
        self.options = {
            'key_prefix': 'session',
            'expire': 1000
            }
        self.options.update(options)
        self.client = conn

    def prefixed(self, sid):
        return self.options['key_prefix'].encode()+sid

    def named(self, sid):
        return self.prefixed(sid)

    def generate_sid(self):
        return uuid4().hex.encode()

    def get_session(self, sid):
        fut = self.client.get(self.named(sid))
        return fut

    @gen.coroutine
    def set_session(self, sid, session_data):
        expiry = self.options['expire']
        yield self.client.set(self.named(sid), session_data, expiry)

    def delete_session(self, sid):
        self.client.delete(self.prefixed(sid))

class Session(object):
     
    def __init__(self, session_store, sessionid=None):
        self._store = session_store
        self.conn = False
        logging.info(sessionid)
        self._sessionid = sessionid if sessionid else self._store.generate_sid()
        self._sessiondata = {}
        self.dirty = False

    def get_sessiondata(self):
        info = self._store.get_session(self._sessionid)
        logging.info(info)
        return info

    def insert_info(self, info, handler):
        logging.info(info)
        if info:
            self.conn = True
        else:
            info = {}
        self._sessiondata = info
        self.access(handler)
        return info

    def clear(self):
        self._store.delete_session(self._sessionid)
 
    def access(self, handler):
        logging.info('access')
        access_info = {
                'user': self._sessionid,
                'remote_ip': handler.request.remote_ip,
                'time':'%.6f' % time.time()
                }
        fut = self._store.set_session(
                self._sessionid,
                access_info
                )
        self._sessiondata.update(access_info)
        logging.info(fut)
        return fut
 
    def last_access(self):
        access_info = self._store.get_session(self._sessionid, 'last_access').result()
        return access_info
 
    @property
    def sessionid(self):
        return self._sessionid
 
    def __getitem__(self, key):
        return self._sessiondata[key]
 
    def __setitem__(self, key, value):
        self._sessiondata[key] = value
        self._dirty()
 
    def __delitem__(self, key):
        del self._sessiondata[key]
        self._dirty()
 
    def __len__(self):
        return len(self._sessiondata)
 
    def __contains__(self, key):
        return key in self._sessiondata
 
    def __iter__(self):
        for key in self._sessiondata:
            yield key
 
    def __repr__(self):
        return self._sessiondata.__repr__()
 
    def __del__(self):
        if self.dirty:
            self._save()
 
    def _dirty(self):
        self.dirty = True
        self._save()
 
    def _save(self):
        self._store.set_session(self._sessionid, self._sessiondata)
        self.dirty = False
