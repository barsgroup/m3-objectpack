#coding: utf-8
'''
File: actions.py
Author: Rinat F Sabitov
Description:
'''

import objectpack

from m3.ui.ext import all_components as ext
import ui

class TreeObjectPack(objectpack.ObjectPack):
    """docstring for TreeObjectPack"""

    list_window = ui.BaseTreeListWindow # Форма списка
    select_window = ui.BaseTreeSelectWindow # Форма выбора @UndefinedVariable

    def configure_grid(self, grid):
        super(TreeObjectPack, self).configure_grid(grid)
        get_url = lambda x: x.get_absolute_url() if x else None
        grid.action_data = self.rows_action
        if not self.read_only:
            grid.action_new = self.new_window_action
            grid.action_edit = self.edit_window_action
            grid.action_delete = self.delete_action


