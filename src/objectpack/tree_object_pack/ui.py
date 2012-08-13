#coding: utf-8
'''
File: ui.py
Author: Rinat F Sabitov
Description:
'''

from objectpack.ui import BaseListWindow
from m3.ui.ext.panels import ExtObjectTree
from m3.ui.ext import misc

class BaseObjectTree(ExtObjectTree):
    pass

    def __init__(self, *args, **kwargs):
        super(BaseObjectTree, self).__init__(*args, **kwargs)
        self.store = misc.ExtJsonStore(auto_load=True, root='rows', id_property='id')


class BaseTreeListWindow(BaseListWindow):
    """docstring for BaseTreeListWindow"""
    def _init_components(self):
        """
        создание компонентов
        """
        super(BaseTreeListWindow, self)._init_components()
        self.grid = BaseObjectTree()

class BaseTreeSelectWindow(BaseTreeListWindow):
    pass

