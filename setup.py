# coding: utf-8
import os

from pip.download import PipSession
from pip.req.req_file import parse_requirements
from setuptools import setup, find_packages


def _get_requirements(file_name):
    pip_session = PipSession()
    requirements = parse_requirements(file_name, session=pip_session)

    return tuple(str(requirement.req) for requirement in requirements)


def _read(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except IOError:
        return ''

setup(
    name="m3-objectpack",
    license='MIT',
    description=_read('DESCRIPTION'),
    author="Alexey Pirogov",
    author_email="pirogov@bars-open.ru",
    url="https://bitbucket.org/barsgroup/objectpack",
    classifiers=[
        'Intended Audience :: Developers',
        'Environment :: Web Environment',
        'Natural Language :: Russian',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'License :: OSI Approved :: MIT License',
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        'Framework :: Django :: 1.4',
        'Framework :: Django :: 1.5',
        'Framework :: Django :: 1.6',
        'Framework :: Django :: 1.7',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.11',
    ],
    package_dir={'': 'src'},
    packages=find_packages('src'),
    include_package_data=True,
    long_description=_read('README'),
    install_requires=_get_requirements('REQUIREMENTS'),
    dependency_links=(
        'http://pypi.bars-open.ru/simple/m3-builder',
    ),
    setup_requires=(
        'm3-builder>=1.1,<2',
    ),
    set_build_info=os.path.dirname(__file__),
)
