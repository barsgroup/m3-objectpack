#coding:utf-8
'''
File: actions.py
Author: Rinat F Sabitov
Description:
'''
from functools import partial

import objectpack
from objectpack import tree_object_pack
from objectpack.filters import FilterByField, ColumnFilterEngine

import models


_PF = partial(FilterByField, models.Person)


#==============================================================================
# PersonObjectPack
#==============================================================================
class PersonObjectPack(objectpack.ObjectPack):
    """docstring for PersonObjectPack"""

    model = models.Person
    add_to_desktop = True
    add_to_menu = True

    edit_window = add_window = objectpack.ui.ModelEditWindow.fabricate(model)

    columns = [
        {
            'data_index': 'fullname',
            'header': u'ФИО',
            'sortable': True,
            'sort_fields': ('name', 'surname'),
            'filter': {
                'type': 'string',
                'custom_field': ('name', 'surname')
            }
        },
        {
            'data_index': 'date_of_birth',
            'header': u'Дата рождения',
            'filter': {
                'type': 'date'
            }
        },
        {
            'data_index': 'gender',
            'header': u'Пол',
            'filter': {
                'type': 'list',
                'options': models.Person.GENDERS
            }
        }
    ]


#==============================================================================
# CFPersonObjectPack
#==============================================================================
class CFPersonObjectPack(objectpack.ObjectPack):
    """
    Пак физ.лиц, демонстрирующий использование колоночных фильтров
    """
    title = u'Физические лица (колоночные фильтры)'

    model = models.Person
    _is_primary_for_model = False

    add_to_desktop = True
    add_to_menu = True

    filter_engine_clz = ColumnFilterEngine

    columns = [
        {
            'data_index': 'fullname',
            'header': u'ФИО',
            'sortable': True,
            'sort_fields': ('name', 'surname'),
            'filter': (
                _PF('name', 'name__icontains') &
                _PF('surname', 'surname__icontains')
            )
        },
        {
            'data_index': 'date_of_birth',
            'header': u'Дата рождения',
            'filter': (
                _PF('date_of_birth', 'date_of_birth__gte', tooltip=u'с') &
                _PF('date_of_birth', 'date_of_birth__lte', tooltip=u'по')
            )
        },
        {
            'data_index': 'gender',
            'header': u'Пол',
            'filter': _PF('gender')
        }
    ]


#==============================================================================
# BandedColumnPack
#==============================================================================
class BandedColumnPack(objectpack.ObjectPack):
    """Демонстрация Banded Columns"""

    title = u'Группирующие колонки'

    model = models.FakeModel

    width, height = 600, 600
    allow_paging = False

    add_to_desktop = True
    add_to_menu = True

    # Колонка становится группирующей, если имеет параметр columns - список
    # вложенных колонок
    # Строим 11 уровней колонок
    columns = (lambda mk_col: [reduce(
        lambda d, c: {
            'header': u'Группа',
            'columns': [
                mk_col(c),
                d,
                mk_col(c),
            ]
        },
        xrange(2, 12),
        mk_col(1)
    )])(
        lambda idx: {
            'type': 'checkbox',
            'header': '%s' % idx,
            'data_index': 'field%s' % idx,
            'width': 25,
            'fixed': True,
            'filter': {'type': 'string'}
        }
    )


#==============================================================================
# TreePack
#==============================================================================
class TreePack(tree_object_pack.TreeObjectPack):
    """
    Пример пака для работы с моделью-деревом
    """
    model = models.TreeNode

    add_to_desktop = True

    columns = [
        {
            "data_index": "kind",
            "header": u"Вид",
            "searchable": True
        },
        {
            "data_index": "name",
            "header": u"Кличка"
        }
    ]
