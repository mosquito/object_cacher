# encoding: utf-8

import copy
from functools import wraps
import os
import tempfile
import time
import uuid
import logging
import traceback

try:
    import cPickle as pickle
except ImportError:
    import pickle

log = logging.getLogger('objectcacher')

__author__ = 'mosquito'


class LazyString(object):
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return self.func(*self.args, **self.kwargs)


class ObjectCacher(object):
    _CACHE = dict()
    _EXPIRATIONS = dict()

    @staticmethod
    def get_oid(hashable):
        return str(uuid.uuid3(uuid.NAMESPACE_OID, str(hashable)))

    def __init__(self, ignore_self=False, timeout=60, oid=None, **kwargs):
        if not oid:
            oid = str(uuid.uuid4())

        log.debug('Create cacher for key "%s" and func: %s',
                  oid, LazyString(lambda: traceback.extract_stack()[-2])
        )

        uoid = self.get_oid(oid)
        if uoid in self._CACHE:
            raise KeyError('Key must be unique but key: "{0}" already exists in cache'.format(oid))
        self.oid = uoid

        self._CACHE[self.oid] = dict()
        self._EXPIRATIONS[self.oid] = dict()
        self.expirations = self._EXPIRATIONS[self.oid]
        self.cache = self._CACHE[self.oid]
        self.timeout = timeout
        self.ignore_self = ignore_self

    def copy(self, obj):
        return copy.deepcopy(obj)

    def is_expired(self, key):
        ts = self.expirations.get(key, None)
        return time.time() > (ts + self.timeout) if ts else True

    def set_ts(self, key):
        self.expirations[key] = time.time()

    def store(self, key, value):
        self.cache[key] = value

    def restore(self, key):
        return self.copy(self.cache[key])

    def check_cache(self, key):
        return key in self.cache

    def __call__(self, func):
        @wraps(func)
        def wrap(*args, **kwargs):
            if self.ignore_self:
                arg_tuple = tuple(args[1:])
            else:
                arg_tuple = tuple(args)

            key = str(hash(tuple((arg_tuple, tuple(kwargs.items())))))

            if self.is_expired(key) and key in self.cache:
                self.cache.pop(key)

            if self.check_cache(key):
                value = self.restore(key)
                log.debug('[%s] Returning from cache key: %s, value: %s', self.oid, key, repr(value))
                return value
            else:
                data = func(*args, **kwargs)
                self.store(key=key, value=data)
                self.set_ts(key=key)
                log.debug('[%s] Storing to cache key: %s, value: %s', self.oid, key, repr(data))
                return self.copy(data)

        wrap.cache_key = self.oid
        return wrap

    @classmethod
    def invalidate(cls, oid, key=None):
        if oid in cls._CACHE:
            if key is not None:
                if key in cls._CACHE[oid] and key in cls._EXPIRATIONS[oid]:
                    cls._CACHE[oid].pop(key)
                    cls._EXPIRATIONS[oid].pop(key)
                    return True
                else:
                    return False
            else:
                for k in cls._CACHE[oid].keys():
                    cls._CACHE[oid].pop(k)
                for k in cls._EXPIRATIONS[oid].keys():
                    cls._EXPIRATIONS[oid].pop(k)
                return True
        else:
            raise KeyError('Hash key not registered')


class ObjectPersistentCacher(ObjectCacher):
    CACHE_DIR = tempfile.gettempdir()

    def __init__(self, ignore_self=False, timeout=60, oid=None, **kwargs):
        super(ObjectPersistentCacher, self).__init__(ignore_self, timeout, oid, **kwargs)

        self.cache_path = os.path.join(self.CACHE_DIR, self.oid)

        if not (os.path.exists(self.cache_path) and os.path.isdir(self.cache_path)):
            os.makedirs(self.cache_path, mode=0775)

        for fname in os.listdir(self.cache_path):
            if os.path.isfile(os.path.join(self.cache_path, fname)):
                self.cache[fname] = True

    def store(self, key, value):
        if not os.path.exists(self.cache_path):
            os.makedirs(self.cache_path, mode=0775)

        pickle.dump(value, open(os.path.join(self.cache_path, key), 'w+'))
        self.cache[key] = True

    def restore(self, key):
        data = pickle.load(open(os.path.join(self.cache_path, key), 'rb'))
        self.cache[key] = True
        return data

    def is_expired(self, key):
        try:
            fname = os.path.join(self.cache_path, key)
            st_mode, st_ino, st_dev, st_nlink, st_uid, st_gid, st_size, st_atime, st_mtime, st_ctime = os.stat(fname)
            ts = st_mtime
        except OSError:
            return True

        return time.time() > (ts + self.timeout) if ts else True

    @classmethod
    def invalidate(cls, oid, key=None):
        if oid in cls._CACHE:
            path = os.path.join(cls.CACHE_DIR, oid)
            if key is not None:
                fname = os.path.join(path, key)
                if os.path.exists(fname) and key in cls._CACHE[oid]:
                    os.remove(fname)
                    cls._CACHE[oid].pop(key)
                    return True
                else:
                    return False
            else:
                for k in cls._CACHE[oid].keys():
                    fname = os.path.join(path, k)
                    os.remove(fname)
                    cls._CACHE[oid].pop(k)
                return True
        else:
            raise KeyError('Hash key not registered')


class ObjectRedisCacher(ObjectCacher):
    # Set the redis connection there
    REDIS = None

    def _redis_key(self, key="*"):
        return "{0}/{1}".format(self.oid, key)

    def store(self, key, value):
        key = self._redis_key(key)
        self.REDIS.set(key, pickle.dumps(value))

    def set_ts(self, key):
        self.REDIS.expire(self._redis_key(key), self.timeout)

    def restore(self, key):
        return pickle.loads(self.REDIS.get(self._redis_key(key)))

    def check_cache(self, key):
        return self.REDIS.exists(self._redis_key(key))

    def is_expired(self, key):
        return self.check_cache(key)

    @classmethod
    def invalidate(cls, oid, key=None):
        if oid in cls._CACHE:
            if key is not None:
                for key in cls.REDIS.keys('{0}/*'.format(oid)):
                    cls.REDIS.delete(key)
                    cls._CACHE[oid] = {}
                return True
            else:
                for k in cls._CACHE[oid].keys():
                    cls.REDIS.delete(key)
                    cls._CACHE[oid].pop(k)
                return True
        else:
            raise KeyError('Hash key not registered')
