# coding:utf-8
"""
:Created: 23.07.2012

:Author: pirogov

.. contents::

objectpack - библиотека для экстремально-быстрой разработки простых \
справочников, основанная на m3-core и m3-ext3.
"""

from version import __version__

from actions import (

    BasePack,
    BaseAction,
    BaseWindowAction,

    ObjectListWindowAction,
    ObjectSelectWindowAction,
    ObjectEditWindowAction,
    ObjectAddWindowAction,
    ObjectSaveAction,
    ObjectRowsAction,
    ObjectDeleteAction,
    ObjectPack,

    SelectorWindowAction,

    multiline_text_window_result,
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
    ObjectGridTab,
    ObjectTab,

    ColumnsConstructor,
    model_fields_to_controls,
)

from tools import (
    extract_int,
    extract_int_list,
    extract_date,

    str_to_date,

    collect_overlaps,

    modify,
    modifier,

    ModelCache,
    QuerySplitter,
    TransactionCM
)

from models import (
    VirtualModel,
    VirtualModelManager,

    ModelProxy,
    model_proxy_metaclass,
)

import observer

from desktop import uificate_the_controller

from exceptions import ValidationError, OverlapError

import column_filters

import filters
