from uuid import uuid4
import time, logging
from tornado.concurrent import Future

class MemcacheStore(object):
    def __init__(self, conn, **options):
        self.options = {
            'key_prefix': 'session',
            'expire': 7200
            }
        self.options.update(options)
        self.client = conn

    def prefixed(self, sid):
        return '%s_%s' % (self.options['key_prefix'], sid)

    def named(self, sid, name):
        return '{}_{}'.format(self.prefixed(sid), name)

    def generate_sid(self):
        return uuid4()

    def get_session(self, sid, name):
        logging.info(self.named(sid, name))
        return self.client.get(self.named(sid, name))

    def set_session(self, sid, session_data, name):
        expiry = self.options['expire']
        return self.client.set(self.named(sid,name), session_data, expiry)

    def delete_session(self, sid):
        self.client.delete(self.prefixed(sid))

class Session:
 
    def __init__(self, session_store, sessionid=None):
        self._store = session_store
        logging.info(sessionid)
        self._sessionid = sessionid if sessionid else self._store.generate_sid()
        self.__sessiondata = self._store.get_session(self._sessionid, 'data')
        self.dirty = False

    @property
    def _sessiondata(self):
        logging.info(self.__sessiondata)
        info = self.__sessiondata.result()
        logging.info(info)
        return info
 
    def clear(self):
        self._store.delete_session(self._sessionid)
 
    def access(self, remote_ip):
        access_info = {'remote_ip':remote_ip, 'time':'%.6f' % time.time()}
        self._store.set_session(
                self._sessionid,
                'last_access',
                access_info
                )
 
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
 
    def _save(self):
        self._store.set_session(self._sessionid, self._sessiondata, 'data')
        self.dirty = False
