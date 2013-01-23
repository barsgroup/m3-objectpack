#coding:utf-8
'''
File: actions.py
Author: Rinat F Sabitov
Description:
'''
import objectpack

import models


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
        {'data_index': 'date_of_birth', 'header': u'Дата рождения',
            'filter': {
                'type': 'date'
            }
        },
    ]

    def __init__(self):
        super(PersonObjectPack, self).__init__()
        self.list_window_action.short_name = 'foo'


#==============================================================================
# PersonObjectPack
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
    )])(lambda idx: {
        'header': '%s' % idx,
        'data_index': 'field%s' % idx,
        'width': 25,
        'fixed': True,
        'filter': {'type': 'string'}
    })
