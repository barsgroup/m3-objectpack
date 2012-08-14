#coding: utf-8
'''
File: ui.py
Author: Rinat F Sabitov
Description:
'''

from objectpack.ui import BaseListWindow, BaseSelectWindow
from m3.ui.ext.panels import ExtObjectTree
from m3.ui.ext import misc
from m3.ui.ext.containers.grids import ExtGridColumn

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

class BaseTreeSelectWindow(BaseSelectWindow):
    #column_name_on_select = 'shortname'
    def _init_components(self):
        """
        создание компонентов
        """
        super(BaseTreeSelectWindow, self)._init_components()
        self.grid = BaseObjectTree()
        self.grid.dblclick_handler = 'selectValue'
        self.grid.columns.append(ExtGridColumn(data_index='__unicode__',
            hidden=True))

    def set_params(self, params):
        """
        установка параметров окна
        """
        super(BaseTreeSelectWindow, self).set_params(params)
        self.template_globals = 'tree-select-window.js'

