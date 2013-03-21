# -*- coding: utf-8 -*-

import inspect


def _name_class(clazz):
    """
    Генерация имени для класса
    """
    return '%s/%s' % (
        inspect.getmodule(clazz).__package__, clazz.__name__)


def name_action(action, pack_name=None):
    """
    Генерация полного имени для @action
    @pack_name - имя пака (если не указано - генерится)
    """
    pack_name = pack_name or _name_class(action.parent.__class__)
    # имя будет иметь вид "пакет/КлассПака/КлассAction"
    return '%s/%s' % (pack_name, action.__class__.__name__)
