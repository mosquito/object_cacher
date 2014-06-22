# encoding: utf-8

import copy
import os
import pickle
import tempfile
import time
import uuid
import logging

log = logging.getLogger('objectcacher')

__author__ = 'mosquito'

class ObjectCacher(object):
    _CACHE = dict()
    _EXPIRATIONS = dict()

    @staticmethod
    def get_oid(hashable):
        return str(uuid.uuid3(uuid.NAMESPACE_OID, str(hashable)))

    def __init__(self, ignore_self=False, timeout=60, oid=None, **kwargs):
        if not oid:
            self.oid = str(uuid.uuid4())
        else:
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

    def __call__(self, func):
        def wrap(*args, **kwargs):
            if self.ignore_self:
                arg_tuple = tuple(args[1:])
            else:
                arg_tuple = tuple(args)

            key = str(hash(tuple((arg_tuple, tuple(kwargs.items())))))

            if self.is_expired(key) and key in self.cache:
                self.cache.pop(key)

            if key in self.cache:
                value = self.restore(key)
                log.debug('Returning from cache key: {0}, value: {1}'.format(key, repr(value)))
                return value
            else:
                data = func(*args, **kwargs)
                self.store(key=key, value=data)
                self.set_ts(key=key)
                log.debug('Storing to cache key: {0}, value: {1}'.format(key, repr(data)))
                return self.copy(data)

        wrap.cache_key = self.oid
        return wrap

    @classmethod
    def invalidate(cls, hash_key, key=None):
        if hash_key in cls._CACHE:
            if key is not None:
                if key in cls._CACHE[hash_key] and key in cls._EXPIRATIONS[hash_key]:
                    cls._CACHE[hash_key].pop(key)
                    cls._EXPIRATIONS[hash_key].pop(key)
                    return True
                else:
                    return False
            else:
                for k in cls._CACHE[hash_key].keys():
                    cls._CACHE[hash_key].pop(k)
                for k in cls._EXPIRATIONS[hash_key].keys():
                    cls._EXPIRATIONS[hash_key].pop(k)
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
    def invalidate(cls, hash_key, key=None):
        if hash_key in cls._CACHE:
            path = os.path.join(cls.CACHE_DIR, hash_key)
            if key is not None:
                fname = os.path.join(path, key)
                if os.path.exists(fname) and key in cls._CACHE[hash_key]:
                    os.remove(fname)
                    cls._CACHE[hash_key].pop(key)
                    return True
                else:
                    return False
            else:
                for k in cls._CACHE[hash_key].keys():
                    fname = os.path.join(path, k)
                    os.remove(fname)
                    cls._CACHE[hash_key].pop(k)
                return True
        else:
            raise KeyError('Hash key not registered')
