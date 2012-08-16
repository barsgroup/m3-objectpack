#coding:utf-8
'''
Created on July 23, 2012

@author: pirogov
'''

__version__ = '0.5.1'

from actions import (
    BaseWindowAction,
    ObjectListWindowAction,
    ObjectSelectWindowAction,
    ObjectEditWindowAction,
    ObjectSaveAction,
    ObjectRowsAction,
    ObjectDeleteAction,
    ObjectPack,

    SelectorWindowAction,
)

from slave_object_pack import SlavePack
from dictionary_object_pack import DictionaryObjectPack
from tree_object_pack import TreeObjectPack


from tree_object_pack import (
    BaseTreeSelectWindow,
    BaseTreeListWindow
)


from ui import (
    BaseWindow,
    BaseEditWindow,
    BaseSelectWindow,
    BaseListWindow,

    ModelEditWindow,

    TabbedWindow,
    TabbedEditWindow,
    WindowTab,

    ColumnsConstructor,
    model_fields_to_controls,
)

from tools import (
    extract_int,
    extract_int_list,
    modify,
    modifier,
)

from models import (
    VirtualModel,
    VirtualModelManager,

    ModelProxy,
    model_proxy_metaclass,
)

import observer

class OverlapError(Exception):
    '''
    Исключние пересечения интервальных моделей
    '''
    def __init__(self, objects, header=(
            u'Имеются пересечения со следующими записями:')):
        assert objects, u"Не указаны объекты, с которыми произошло пересечение!"
        self._header = header
        self._objects = objects

    def __str__(self):
        return unicode(self)

    def __unicode__(self):
        return u'\n- '.join([self._header] + map(unicode, self._objects))

class ValidationError(Exception):
    '''
    Исключение валидации
    '''
    def __init__(self, text):
        assert text, u'Не указан текст сообщения'
        self._text = text

    def __str__(self):
        return unicode(self)

    def __unicode__(self):
        return unicode(self._text)
