#coding: utf-8
'''
File: actions.py
Author: Rinat F Sabitov
Description:
'''

import objectpack

from m3.ui.ext import all_components as ext
import ui
import copy
from m3.ui import actions as m3_actions

class TreeObjectPack(objectpack.ObjectPack):
    """docstring for TreeObjectPack"""

    list_window = ui.BaseTreeListWindow # Форма списка
    select_window = ui.BaseTreeSelectWindow # Форма выбора @UndefinedVariable

    def __init__(self, *args, **kwargs):
        super(TreeObjectPack, self).__init__(*args, **kwargs)
        self.replace_action('rows_action', TreeObjectRowsAction())

    def get_rows_query(self, request, context):
        result = super(TreeObjectPack, self).get_rows_query(request, context)
        current_node_id = int(getattr(context, self.id_param_name, -1))
        if not current_node_id>0:
            current_node_id = None
        result = result.filter(parent__id=current_node_id)
        return result

    def configure_grid(self, grid):
        super(TreeObjectPack, self).configure_grid(grid)
        get_url = lambda x: x.get_absolute_url() if x else None
        grid.action_data = self.rows_action
        if not self.read_only:
            grid.action_new = self.new_window_action
            grid.action_edit = self.edit_window_action
            grid.action_delete = self.delete_action

    def create_edit_window(self, create_new, request, context):
        win = super(TreeObjectPack, self).create_edit_window(create_new, request, context)
        if hasattr(context, 'parent_id'):
            win.form.from_object(dict(parent_id=int(context.parent_id)))
        return win


class TreeObjectRowsAction(objectpack.ObjectRowsAction):
    """docstring for TreeObjectRowsAction"""

    def set_query(self):
        """docstring for set_query"""
        super(TreeObjectRowsAction, self).set_query()
        self._parents = self.parent.model.objects.filter(
            parent__isnull=False,
        ).values_list('parent__id', flat=True)

    def prepare_object(self, obj):
        """docstring for prepare_object"""
        obj = super(TreeObjectRowsAction, self).prepare_object(obj)
        obj['leaf'] = int(obj['id']) not in self._parents
        return obj

    def run(self, *args, **kwargs):
        result = super(TreeObjectRowsAction, self).run(*args, **kwargs)
        data = result.data.get('rows',[])
        return m3_actions.PreJsonResult(data)

