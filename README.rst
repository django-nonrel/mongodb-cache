What is it
==========

A cache backend similar to Django's built-in ``db`` cache backend,
but for MongoDB rather than for SQL databases.

How to use it
=============
It's easy::

   CACHE_BACKEND = 'django_mongodb_cache://collection_name'

(You need the very latest Django trunk.)
