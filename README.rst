What is it
==========

A cache backend similar to Django's built-in ``db`` cache backend,
but for MongoDB rather than for SQL databases.

How to use it
=============
It's easy::

``` python
CACHES = {
    'default' : {
        'BACKEND' : 'django_mongodb_cache.MongoDBCache'
    }
}```

**Requires** `Django MongoDB Engine`_ 0.4 or later (currently unreleased, use Git version)

.. _Django MongoDB Engine: https://github.com/django-mongodb-engine/mongodb-engine
