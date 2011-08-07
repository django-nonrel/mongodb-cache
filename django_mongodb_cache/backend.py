import time
from django.core.cache.backends.db import BaseDatabaseCache
from django.db import connections, router
try:
    import cPickle as pickle
except ImportError:
    import pickle

import pymongo
import bson

class MongoDBCache(BaseDatabaseCache):
    def validate_key(self, key):
        if '.' in key or '$' in key:
            raise ValueError("Cache keys must not contain '.' or '$' "
                             "if using MongoDB cache backend")
        super(MongoDBCache, self).validate_key(key)

    def get(self, key, default=None, version=None, raw=False, raw_key=False):
        if not raw_key:
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
        except bson.errors.InvalidDocument:
            # value can't be serialized to BSON, fall back to pickle.

            # TODO: Suppress PyMongo warning here by writing a PyMongo patch
            # that allows BSON to be passed as document to .save
            pickle_blob = pickle.dumps(new_document.pop('v'), protocol=2)
            new_document['p'] = bson.binary.Binary(pickle_blob)
            collection.save(new_document)

        return True

    def incr(self, key, delta=1, version=None):
        key = self.make_key(key, version=version)
        collection = self._collection_for_write()
        update_args = [{'_id': key}, {'$inc': {'v': delta}}]

        if hasattr(pymongo.collection.Collection, 'find_and_modify'):
            # XXX change this to tuple/int comparison once
            # there's a pymongo.version tuple equivalent
            new_document = collection.find_and_modify(*update_args, new=True, fields=['v'])
            if new_document is None:
                raise ValueError("Key %r not found" % key)
            return new_document['v']
        else:
            document = self.get(key, version=version, raw=True, raw_key=True)
            if document is None:
                raise ValueError("Key %r not found" % key)
            new_value = document['v'] + delta
            collection.update(*update_args)
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
                            .sort('e', pymongo.ASCENDING) \
                            .skip(count / self._cull_frequency).limit(1)[0]
            collection.remove({'e' : {'$lt' : cut['e']}}, safe=True)

    def _collection_for_read(self):
        db = router.db_for_read(self.cache_model_class)
        return connections[db].database[self._table]

    def _collection_for_write(self):
        db = router.db_for_write(self.cache_model_class)
        return connections[db].database[self._table]
