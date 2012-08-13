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

