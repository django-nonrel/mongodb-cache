from setuptools import setup, find_packages
import codecs

CLASSIFIERS = [
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Programming Language :: Python',
    'Operating System :: OS Independent',
    'Topic :: Cache',
    'Topic :: Database',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

setup(
    name='django_mongodb_cache',
    version='0.1',
    author='Jonas Haag',
    author_email='jonas@lophus.org',
    url='http://github.com/django-mongodb-engine/mongodb-cache',
    license='2-clause BSD',
    description="A Django MongoDB cache backend",
    long_description=None,

    platforms=['any'],
    install_requires=['django_mongodb_engine>=0.2'],

    packages=['django_mongodb_cache'],
    include_package_data=True,
    classifiers=CLASSIFIERS
)
