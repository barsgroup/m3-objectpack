# coding: utf-8
# pylint: disable=not-context-manager, relative-import
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from os import environ

from fabric.api import local
from fabric.context_managers import hide
from fabric.context_managers import lcd
from fabric.decorators import task

from ._settings import SRC_DIR
from ._settings import TESTS_DIR
from ._utils import nested


@task
def tests():
    """Запуск тестов."""

    pythonpath = environ.get('PYTHONPATH', '')
    environ['PYTHONPATH'] = ':'.join((pythonpath, SRC_DIR))

    with nested(
        hide('running'),
        lcd(TESTS_DIR)
    ):

        local('./runtests.sh')
