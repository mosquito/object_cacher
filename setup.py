# encoding: utf-8

from __future__ import absolute_import, print_function

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


__version__ = '0.1.1'
__author__ = 'Dmitry Orlov <me@mosquito.su>'


setup(name='object_cacher',
    version=__version__,
    author=__author__,
    author_email='me@mosquito.su',
    license="MIT",
    description="Simple objects/methods results cacher with optional persistent cacheing.",
    platforms="all",
    url="http://github.com/mosquito/objectcacher",
    classifiers=[
      'Environment :: Console',
      'Programming Language :: Python',
    ],
    long_description=open('README.rst').read(),
    packages=[
      '.',
    ],
)
