# coding: utf-8
"""
UI для работы с древовидными списками
Author: Rinat F Sabitov
"""

from objectpack.ui import BaseListWindow, BaseSelectWindow
from m3_ext.ui.panels import ExtObjectTree
from m3_ext.ui import misc


class BaseObjectTree(ExtObjectTree):
    """
    Визуальный элемент "Дерево"
    """
    def __init__(self, *args, **kwargs):
        super(BaseObjectTree, self).__init__(*args, **kwargs)
        self.store = misc.ExtJsonStore(
            auto_load=True, root='rows', id_property='id')


class BaseTreeListWindow(BaseListWindow):
    """
    Окно отбражения объектов в виде деревовидного списка
    """
    def _init_components(self):
        """
        создание компонентов
        """
        super(BaseTreeListWindow, self)._init_components()
        self.grid = BaseObjectTree()


class BaseTreeSelectWindow(BaseSelectWindow):
    """
    Окно выбора объекта из древовидного списка
    """

    def _init_components(self):
        """
        создание компонентов
        """
        super(BaseTreeSelectWindow, self)._init_components()
        self.grid = BaseObjectTree()
        self.grid.dblclick_handler = 'selectValue'

    def set_params(self, params):
        """
        установка параметров окна
        """
        super(BaseTreeSelectWindow, self).set_params(params)
        self.template_globals = 'tree-select-window.js'
