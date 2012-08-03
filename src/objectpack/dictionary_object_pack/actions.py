#coding: utf-8
'''
File: actions.py
Author: Rinat F Sabitov
Description:
'''

import objectpack
from django.utils.translation import ugettext as _


class DictionaryObjectPack(objectpack.ObjectPack):
    """object pack for simple dictionary models"""
    add_to_menu = True

    columns = [
        {'data_index': 'code', 'header': _(u'код'), 'searchable': True},
        {'data_index': 'name', 'header': _(u'наименование'), 'searchable': True},
    ]

    def __init__(self, *args, **kwargs):
        """docstring for __init__"""
        self.edit_window = self.add_window = objectpack.ui.ModelEditWindow.fabricate(self.model)
        super(DictionaryObjectPack, self).__init__(*args, **kwargs)

    def extend_menu(self, menu):
        """docstring for extend_menu"""
        if self.add_to_menu:
            return menu.dicts(menu.Item(self.title, self))

