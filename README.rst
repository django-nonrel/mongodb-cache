What is it
==========

A cache backend similar to Django's built-in ``db`` cache backend,
but for MongoDB rather than for SQL databases.

How to use it
=============
It's easy::

    CACHES = {
        'default' : {
            'BACKEND' : 'django_mongodb_cache.MongoDBCache'
        }
    }

Requirements
============
* `Django MongoDB Engine`_ 0.4 or later
* `PyMongo` 2.0 or later

.. _Django MongoDB Engine: http://django-mongodb.org
.. _PyMongo: http://api.mongodb.org/python/current/
