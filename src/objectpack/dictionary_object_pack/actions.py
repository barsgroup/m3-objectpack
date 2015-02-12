# coding: utf-8
"""
File: actions.py
Author: Rinat F Sabitov
Description:
"""

import objectpack


class DictionaryObjectPack(objectpack.ObjectPack):
    """
    Набор действий для простых справочников
    """
    add_to_menu = True

    columns = [
        {
            'data_index': 'code',
            'header': u'код',
            'searchable': True
        },
        {
            'data_index': '__unicode__',
            'header': u'наименование',
            'searchable': True
        },
    ]

    def __init__(self, *args, **kwargs):
        """
        Инициализация
        """
        if not any([self.edit_window, self.add_window]):
            self.edit_window = self.add_window = (
                objectpack.ui.ModelEditWindow.fabricate(self.model)
            )
        super(DictionaryObjectPack, self).__init__(*args, **kwargs)

    def extend_menu(self, menu):
        """
        Интеграция в Главное Меню
        """
        if self.add_to_menu:
            return menu.dicts(menu.Item(self.title, self))
