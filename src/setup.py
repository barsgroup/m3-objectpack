# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages


def read(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except IOError:
        return ''

setup(
    name="objectpack",
    version="0.7.2.8",
    description=read('DESCRIPTION'),
    license="GPL",
    keywords="django m3 m3-contrib",

    author="Alexey Pirogov",
    author_email="pirogov@bars-open.ru",

    maintainer='Alexey V Pirogov, Rinat F Sabitov',
    maintainer_email='rinat.sabitov@gmail.com',

    url="https://src.bars-open.ru/py/m3/m3_contrib/objectpack",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Framework :: Django',
        'Environment :: Web Environment',
        'Natural Language :: Russian',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    packages=find_packages(exclude=['example', 'example.*']),
    install_requires=[],
    include_package_data=True,
    zip_safe=False,
    long_description=read('README'),
)
