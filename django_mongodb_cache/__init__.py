__version__ = (0, 2, 0)
__author__ = "Jonas Haag <jonas@lophus.org>"

from backend import MongoDBCache

# Django < 1.3 compatibility
CacheClass = MongoDBCache
