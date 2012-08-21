#coding: utf-8
"""
Действия для работы с древовидными справочниками
Author: Rinat F Sabitov
"""

import objectpack

from m3.ui.ext import all_components as ext
from m3.ui import actions as m3_actions

import ui
import copy


class TreeObjectPack(objectpack.ObjectPack):
    """
    Набор действий для работы с объектами,
    находящимися в древовидной иерархии.
    """

    list_window = ui.BaseTreeListWindow
    select_window = ui.BaseTreeSelectWindow

    def __init__(self, *args, **kwargs):
        super(TreeObjectPack, self).__init__(*args, **kwargs)
        self.replace_action('rows_action', TreeObjectRowsAction())


    def get_rows_query(self, request, context):
        result = super(TreeObjectPack, self).get_rows_query(request, context)
        # данные подгружаются "поуровнево"
        # для загрузки следующего уровня - поддерева, запрос содержит id узла,
        # из которого поддерево "растет"
        current_node_id = objectpack.extract_int(request, self.id_param_name)
        if current_node_id < 0:
            # если корневой узел поддерева не указан, будут выводиться
            # деревья самого верхнего уровня (не имеющие родителей)
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
    """
    Получение данных для древовидного списка объектов
    """

    def set_query(self):
        """docstring for set_query"""
        super(TreeObjectRowsAction, self).set_query()
        # получение списка id узлов дерева, имеющих ответвления
        self._parents = self.parent.model.objects.filter(
            parent__isnull=False,
        ).values_list('parent__id', flat=True)


    def prepare_object(self, obj):
        """docstring for prepare_object"""
        obj = super(TreeObjectRowsAction, self).prepare_object(obj)
        # признак "ветка"/"лист"
        obj['leaf'] = int(obj['id']) not in self._parents
        return obj


    def run(self, *args, **kwargs):
        result = super(TreeObjectRowsAction, self).run(*args, **kwargs)
        data = result.data.get('rows',[])
        return m3_actions.PreJsonResult(data)
