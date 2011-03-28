# coding: utf-8
from django.test import TestCase
from django.core.cache import get_cache
from regressiontests.cache.tests import BaseCacheTests

def _monkeypatch_zlib():
    """ Make zlib.compress return a bson.binary.Binary instance """
    import zlib
    from bson.binary import Binary
    _compress = zlib.compress
    zlib.compress = lambda *args, **kwargs: Binary(_compress(*args, **kwargs))

class MongoCacheTests(TestCase, BaseCacheTests):
    def setUp(self):
        self.cache = get_cache('django_mongodb_cache://testtable?max_entries=30')

    def test_invalid_key(self):
        for methods, args in [
            (['set', 'add', 'incr', 'decr'], [42]),
            (['get', 'delete'], [])
        ]:
            for method in methods:
                self.assertRaises(ValueError, getattr(self.cache, method), 'key-with.dot', *args)
                self.assertRaises(ValueError, getattr(self.cache, method), 'key-with-$dollar', *args)

    def test_cull(self):
        self.perform_cull_test(50, 29)

    def test_zero_cull(self):
        self.cache = get_cache('django_mongodb_cache://testtable2?max_entries=30&cull_frequency=0')
        self.perform_cull_test(50, 18)

_monkeypatch_zlib()
