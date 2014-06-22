import tornado.ioloop
import tornado.iostream
import socket
import random
import functools
import collections
import logging
import pickle
import types, time
from tornado.concurrent import Future


class Client(object):

    _FLAG_PICKLE  = 1<<0
    _FLAG_INTEGER = 1<<1
    _FLAG_LONG    = 1<<2

    def __init__(self, servers = ["127.0.0.1:11211"], debug=0, **kwargs):
        self.debug = debug
        self.io_loop = tornado.ioloop.IOLoop.instance()
        self.conn_pool = ConnectionPool(servers, debug=debug, **kwargs)

    def _debug(self, msg):
        if self.debug:
            logging.debug(msg)

    def _info(self, msg):
        if self.debug:
            logging.info(msg)

    def _server(self, key):
        return self.conn_pool.reserve().get_server_for_key(key)

    def get(self, key, callback = lambda rez: rez):
        server = self._server(key)
        in_callback = functools.partial(self._get_callback_write, server=server, callback=callback)
        self._info('in get')
        logging.info('get')
        return server.send_cmd("get {}".format(key).encode(), in_callback)

    def _get_callback_write(self, server, callback):
        in_callback = functools.partial(self._get_callback_read, server=server, callback=callback)
        self._info('in get callback')
        fut = Future()
        def con_close(*ar, **kw):
            new_fut = in_callback(*ar, **kw)
            tornado.concurrent.chain_future(new_fut, fut)
            self._info('get result call')
        server.stream.read_until(b"\r\n", con_close)
        return fut

    def _get_callback_read(self, result, server, callback):
        self._info("_get_callback_read `%s`" % (result,))
        if result[:3] == b"END":
            logging.info('read_callback_release')
            self.conn_pool.release(server.conn)
            fut = Future()
            fut.set_result(callback(None))
            return fut
        elif result[:5] == b"VALUE":
            flag, length = result.split(b" ")[2:]
            in_callback = functools.partial(
                self._get_callback_value,
                server=server,
                callback=callback,
                flag=int(flag)
            )
            fut = Future()
            def con_close(*ar, **kw):
                self._info('get result call {}'.format(result))
                info = in_callback(*ar, **kw)
                fut.set_result(info)
                return info
            server.stream.read_until(
                b"END", con_close)
            return fut
        else:
            logging.error("Bad response from  memcache >%s<" % (result,))
            logging.info('bad_callback_release')
            self.conn_pool.release(server.conn)
            raise Exception('Bad resp memcached')

    def _get_callback_value(self, result, flag, server, callback):
        result = result.replace(b"\r\nEND", b"")
        logging.info('value_callback_release')
        self.conn_pool.release(server.conn)

        if flag == 0:
            value = result
        elif flag & Client._FLAG_INTEGER:
            value = int(result)
        elif flag & Client._FLAG_LONG:
            value = long(result)
        elif flag & Client._FLAG_PICKLE:
            value = pickle.loads(result)
        callback(value)
        return value

    def get_multi(self, keys, callback):
        pass

    def set(self, key, value, timeout=0, callback = lambda rez: rez):
        logging.info('set')
        assert isinstance(timeout, int)
        self._info('insert key {}'.format(key))

        server = self._server(key)
        flags = 0
        if isinstance(value, str):
            pass
        elif isinstance(value, int):
            flags |= Client._FLAG_INTEGER
            value = str(value).encode()
        else:
            flags |= Client._FLAG_PICKLE
            value = pickle.dumps(value, 2)
        str_info = {
            'key': key,
            'flags': flags,
            'timeout': timeout,
            'length': len(value),
            }
        in_callback = functools.partial(self._set_callback_write, server=server, callback=callback)
        return server.send_cmd("set {key} {flags} {timeout}\
                {length:d}\r\n".format(**str_info).encode()+value, in_callback)

    def _set_callback_write(self, server, callback):
        in_callback = functools.partial(self._set_callback_read, server=server, callback=callback)
        fut = Future()
        def close_con(*ar, **kw):
            new_fut = in_callback(*ar, **kw)
            tornado.concurrent.chain_future(new_fut, fut)
            self._info('set result call')
        server.stream.read_until(b"\r\n", close_con)
        return fut

    def _set_callback_read(self, result, server, callback):
        self._info('read {}'.format(result))
        self.conn_pool.release(server.conn)
        logging.info('set_callback_release')
        fut = Future()
        fut.set_result(callback(result))
        return fut

    def set_multi(self, mapping, callback):
        pass

    def delete(self, key, timeout=0, callback = lambda r: r):
        server = self._server(key)
        cmd = "delete %s" % (key,)
        if timeout:
            cmd += " %d" % (timeout,)

        in_callback = functools.partial(
                self._delete_callback_write,
                callback=callback,
                server=server)
        return server.send_cmd(cmd.encode(), in_callback)

    def _delete_callback_write(self, server, callback):
        in_callback = functools.partial(self._set_callback_read, server=server, callback=callback)
        fut = Future()
        def close_con(*ar, **kw):
            new_fut = in_callback(*ar, **kw)
            tornado.concurrent.chain_future(new_fut, fut)
            self._info('set result call')
        server.stream.read_until(b"\r\n", close_con)
        return fut

    def delete_multi(self, keys, callback):
        pass


class ConnectionPool(object):

    def __init__(self, servers, max_connections=15, debug=0):
        self.pool = [Connection(servers, debug) for i in range(max_connections)]

        self.in_use = collections.deque()
        self.idle = collections.deque(self.pool)

    def reserve(self):
        conn = self.idle.popleft()
        self.in_use.append(conn)
        return conn

    def release(self, conn):
        self.in_use.remove(conn)
        self.idle.append(conn)


class Connection(object):

    def __init__(self, servers, debug=0):
        assert isinstance(servers, list)

        self.hosts = [Host(s, self, debug) for s in servers]

    def get_server_for_key(self, key):
        return self.hosts[hash(key) % len(self.hosts)]

class Host(object):

    def _info(self, msg):
        if self.debug:
            logging.info(msg)

    def __init__(self, host, conn, debug=0):
        self.debug = debug
        self.conn = conn
        self.host = host
        self.port = 11211
        if ":" in self.host:
            parts = self.host.split(":")
            self.host = parts[0]
            self.port = int(parts[1])

        self.sock = None

    def _ensure_connection(self):
        if self.sock:
            return

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((self.host, self.port))
        except socket.error as msg:
            print(msg)
            return None
        self.sock = s
        self.stream = tornado.iostream.IOStream(s)
        self.stream.debug = True

    def close_socket(self, resp):
        self.stream.close()
        self.sock.close()
        self.sock = None

    def send_cmd(self, cmd, callback):
        self._ensure_connection()
        cmd = cmd + "\r\n".encode()
        fut = Future()
        def close_con(*ar, **kw):
            logging.debug('in cmd before call {} {}'.format(cmd , callback))
            new_fut = callback(*ar, **kw)
            self._info('con future {}'.format(new_fut))
            tornado.concurrent.chain_future(new_fut, fut)
        self.stream.write(cmd, close_con)
        fut.add_done_callback(self.close_socket)
        logging.debug('in cmd to que {} {}'.format(cmd , callback))
        return fut

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    value = random.randint(1, 100)
    server = tornado.ioloop.IOLoop.instance()
    c =  Client(["127.0.0.1:11211"], debug=1)
    def _set_cb(res):
        print("\n\nSet callback", res)

        def _get_cb(res):
            print("\n\n\nGet callback!", res)
            c.get("bar", lambda r: logging.info("\n\n\n\nget bar "+str(r)))
            c.delete('foo', 0, lambda r: c.get('foo', lambda r1: logging.info('\n\n\n\nget_deleted \
                {} info {}'.format(r1, r))))

        c.get("foo", _get_cb)

    def stop(*ar, **kw):
        logging.info('\n\n\nStop server {}_{}'.format(ar, kw))
        #server.stop()
    print("\n\n\nSetting value {0}".format(value))
    c.set("foo", value, 0, _set_cb)

    c.set("bara", {'1': '1'}, 1000, lambda res: stop(server))

    def fut_test():
        print("\n\n\nGet value bara\n\n\n =========================\n")
        c.get('bara', lambda res: stop(res))
        #fut tests
        fut = c.set("future", value, 2)
        print("\n\n\nGet value future bara\n\n\n =========================\n")
        fut_get = c.get('bara')
        fut_del = c.delete('bara')
        server.add_future(fut, lambda futur: logging.info('\n\n\n\n\n!!!!!!{}!!!!1\n\n\n'.format(futur.result())))
        server.add_future(fut_get, lambda futur: logging.info('\n\n\n\n\n222!!!{}!!!!1\n\n\n'.format(futur.result())))
        server.add_future(fut_del, lambda futur: logging.info('\n\n\n\n\n333!!!{}!!!!1\n\n\n'.format(futur.result())))

    server.add_timeout(time.time() + 2, fut_test)

    server.start()
