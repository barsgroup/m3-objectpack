#coding: utf-8
'''
File: ui.py
Author: Rinat F Sabitov
Description:
'''

from objectpack.ui import BaseListWindow
from m3.ui.ext.containers.trees import ExtTree

class BaseTreeListWindow(BaseListWindow):
    """docstring for BaseTreeListWindow"""
    def _init_components(self):
        """
        создание компонентов
        """
        super(BaseTreeListWindow, self)._init_components()
        self.grid = ExtTree

class BaseTreeSelectWindow(BaseTreeListWindow):
    pass
