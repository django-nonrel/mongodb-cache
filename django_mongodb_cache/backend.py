import time
from django.core.cache.backends.db import BaseDatabaseCache
from django.db import connections, router
try:
    import cPickle as pickle
except ImportError:
    import pickle

from bson.errors import InvalidDocument
from bson.binary import Binary
from pymongo import ASCENDING

class MongoDBCache(BaseDatabaseCache):
    def validate_key(self, key):
        if '.' in key or '$' in key:
            raise ValueError("Cache keys must not contain '.' or '$' "
                             "if using MongoDB cache backend")
        super(MongoDBCache, self).validate_key(key)

    def get(self, key, default=None, version=None, raw=False):
        key = self.make_key(key, version=version)
        self.validate_key(key)

        collection = self._collection_for_read()
        document = collection.find_one({'_id' : key})

        if document is None:
            return default

        if document['e'] < time.time():
            # outdated document, delete it and pretend it doesn't exist
            collection.remove({'_id' : key})
            return default

        if raw:
            return document

        pickled_obj = document.get('p')
        if pickled_obj is not None:
            return pickle.loads(pickled_obj)
        else:
            return document['v']

    def has_key(self, key, version=None):
        return self.get(key, version=version, raw=True) is not None

    def set(self, key, value, timeout=None, version=None):
        self._base_set(key, value, timeout, version, force_set=True)

    def add(self, key, value, timeout=None, version=None):
        return self._base_set(key, value, timeout, version, force_set=False)

    def _base_set(self, key, value, timeout, version, force_set=False):
        collection = self._collection_for_write()

        if collection.count() > self._max_entries:
            self._cull(collection)

        if not force_set and self.has_key(key, version):
            # do not overwrite existing, non-expired entries.
            return False

        key = self.make_key(key, version=version)
        self.validate_key(key)
        now = time.time()
        expires = now + (timeout or self.default_timeout)
        new_document = {'_id' : key, 'v' : value, 'e' : expires}

        try:
            collection.save(new_document)
        except InvalidDocument:
            # value can't be serialized to BSON, fall back to pickle.

            # TODO: Suppress PyMongo warning here by writing a PyMongo patch
            # that allows BSON to be passed as document to .save
            new_document['p'] = Binary(pickle.dumps(new_document.pop('v'), protocol=2))
            collection.save(new_document)

        return True

    def incr(self, key, delta=1, version=None):
        # TODO: If PyMongo eventually implements findAndModify, use it.
        document = self.get(key, version=version, raw=True)
        # XXX: Two calls into `make_key` here, should be one
        key = self.make_key(key, version=version)
        if document is None:
            raise ValueError("Key %r not found" % key)
        collection = self._collection_for_write()
        new_value = document['v'] + delta
        collection.update({'_id' : key}, {'$inc' : {'v' : delta}})
        return new_value

    def delete(self, key, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)
        self._collection_for_write().remove({'_id' : key})

    def clear(self):
        self._collection_for_write().drop()

    def _cull(self, collection):
        if self._cull_frequency == 0:
            self.clear()
            return

        collection.remove({'e' : {'$lt' : time.time()}})
        # remove all expired entries
        count = collection.count()
        if count > self._max_entries:
            # still too much entries left
            cut = collection.find({}, {'e' : 1}) \
                            .sort('e', ASCENDING) \
                            .skip(count / self._cull_frequency).limit(1)[0]
            collection.remove({'e' : {'$lt' : cut['e']}}, safe=True)

    def _collection_for_read(self):
        db = router.db_for_read(self.cache_model_class)
        return connections[db].database[self._table]

    def _collection_for_write(self):
        db = router.db_for_write(self.cache_model_class)
        return connections[db].database[self._table]
