#coding:utf-8
'''
File: actions.py
Author: Rinat F Sabitov
Description:
'''
import objectpack

import models


#===============================================================================
# PersonObjectPack
#===============================================================================
class PersonObjectPack(objectpack.ObjectPack):
    """docstring for PersonObjectPack"""

    model = models.Person
    add_to_desktop = True
    add_to_menu = True


#===============================================================================
# PersonObjectPack
#===============================================================================
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
    })
