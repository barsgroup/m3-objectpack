'''
File: actions.py
Author: Rinat F Sabitov
Description:
'''

import objectpack

class DictionaryObjectPack(objectpack.ObjectPack):
    """object pack for simple dictionary models"""
    add_to_menu = True

    def __init__(self, *args, **kwargs):
        """docstring for __init__"""
        self.edit_window = self.add_window = objectpack.ui.ModelEditWindow.fabricate(self.model)
        super(DictionaryObjectPack, self).__init__(*args, **kwargs)

    def extend_menu(self, menu):
        """docstring for extend_menu"""
        if self.add_to_menu:
            return menu.dicts(menu.Item(self.title, self))

