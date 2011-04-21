# coding: utf-8
from django.core.cache import get_cache
from regressiontests.cache.tests import DBCacheTests, management

def _monkeypatch_zlib():
    """ Make zlib.compress return a bson.binary.Binary instance """
    import zlib
    from bson.binary import Binary
    _compress = zlib.compress
    zlib.compress = lambda *args, **kwargs: Binary(_compress(*args, **kwargs))

class MongoCacheTests(DBCacheTests):
    backend_name = 'django_mongodb_cache.MongoDBCache'

    def setUp(self):
        # super(...).setUp() calls the 'createcachetable' command which
        # executes SQL initializaton code. Obviously we can't execute any SQL
        # so monkey-patch call_command here to skip this call.
        self._call_command = management.call_command
        def call_command(cmd, *args, **kwargs):
            if cmd != 'createcachetable':
                return _call_command(cmd, *args, **kwargs)
        management.call_command = call_command
        super(MongoCacheTests, self).setUp()

    def tearDown(self):
        management.call_command = self._call_command
        self.cache.clear()

    def test_keys_invalid_on_mongodb(self):
        for methods, args in [
            (['set', 'add', 'incr', 'decr'], [42]),
            (['get', 'delete'], [])
        ]:
            for method in methods:
                self.assertRaises(ValueError, getattr(self.cache, method), 'key-with.dot', *args)
                self.assertRaises(ValueError, getattr(self.cache, method), 'key-with-$dollar', *args)

    def test_old_initialization(self):
        self.cache = get_cache('django_mongodb_cache://%s?max_entries=30&cull_frequency=0' % self._table_name)
        self.perform_cull_test(50, 18)

del DBCacheTests

_monkeypatch_zlib()
