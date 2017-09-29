#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from setuptools import setup, find_packages
import formfield


version = __import__('formfield').get_version()

if sys.argv[-1] == 'publish':
    os.system('python setup.py bdist_wheel upload -r natgeo')
    print("You probably want to also tag the version now:")
    print("  python setup.py tag")
    sys.exit()
elif sys.argv[-1] == 'tag':
    cmd = "git tag -a %s -m 'version %s';git push --tags" % (version, version)
    os.system(cmd)
    sys.exit()


def read_file(filename):
    """Read a file into a string"""
    p = os.path.abspath(os.path.dirname(__file__))
    filepath = os.path.join(p, filename)
    try:
        return open(filepath).read()
    except IOError:
        return ''


def get_readme():
    """Return the README file contents. Supports text,rst, and markdown"""
    for name in ('README', 'README.rst', 'README.md'):
        if os.path.exists(name):
            return read_file(name)
    return ''

# Use the docstring of the __init__ file to be the description
DESC = " ".join(formfield.__doc__.splitlines()).strip()

setup(
    name="django-formfield",
    version=formfield.get_version().replace(' ', '-'),
    url='http://github.com/jsoa/django-formfield/',
    author='Jose Soares',
    author_email='jose@linux.com',
    description=DESC,
    long_description=get_readme(),
    packages=find_packages(exclude=('example', 'example.*', )),
    include_package_data=True,
    install_requires=read_file('requirements.txt'),
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Framework :: Django',
    ],
)
