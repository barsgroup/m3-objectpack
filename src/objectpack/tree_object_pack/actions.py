# coding: utf-8
"""
Действия для работы с древовидными справочниками
Author: Rinat F Sabitov
"""

import objectpack

from objectpack import tools

from m3 import actions as m3_actions

import ui


class TreeObjectPack(objectpack.ObjectPack):
    """
    Набор действий для работы с объектами,
    находящимися в древовидной иерархии.
    """
    # поле модели - ссылка на родителя
    parent_field = 'parent'

    list_window = ui.BaseTreeListWindow
    select_window = ui.BaseTreeSelectWindow

    def __init__(self, *args, **kwargs):
        super(TreeObjectPack, self).__init__(*args, **kwargs)
        self.replace_action('rows_action', TreeObjectRowsAction())
        self.autocomplete_action = objectpack.ObjectRowsAction()
        self.actions.append(self.autocomplete_action)

    def get_rows_query(self, request, context):
        result = super(TreeObjectPack, self).get_rows_query(request, context)
        # данные грузятся поуровнево только есть не указан фильтр
        filter_in_params = bool(request.REQUEST.get('filter'))
        if not filter_in_params:
            # данные подгружаются "поуровнево", для чего
            # запрос содержит id узла, из которого поддерево "растет"
            current_node_id = objectpack.extract_int(
                request, self.id_param_name)
            if current_node_id < 0:
                # если корневой узел поддерева не указан, будут выводиться
                # деревья самого верхнего уровня (не имеющие родителей)
                current_node_id = None
            result = result.filter(
                **{('%s__id' % self.parent_field): current_node_id})
        return result

    def configure_grid(self, grid):
        super(TreeObjectPack, self).configure_grid(grid)
        grid.action_data = self.rows_action
        if not self.read_only:
            grid.action_new = self.new_window_action
            grid.action_edit = self.edit_window_action
            grid.action_delete = self.delete_action

    def create_edit_window(self, create_new, request, context):
        win = super(TreeObjectPack, self).create_edit_window(
            create_new, request, context)
        parent_id = getattr(context, 'parent_id', None)
        if context.parent_id is not None:
            win.form.from_object({'parent_id': parent_id})
        return win

    def save_row(self, obj, create_new, request, context):
        parent_id = getattr(context, 'parent_id', None)
        setattr(obj, '%s_id' % self.parent_field, parent_id)
        obj.save()

    def declare_context(self, action):
        decl = super(TreeObjectPack, self).declare_context(action)
        if action is self.new_window_action:
            decl[self.id_param_name]['default'] = 0
        if action in (
            self.edit_window_action,
            self.new_window_action,
            self.save_action
        ):
            # id может и не прийти,
            # если добавление производится в корень
            decl['parent_id'] = {'type': tools.int_or_none, 'default': None}
        return decl

    def get_autocomplete_url(self):
        return self.autocomplete_action.get_absolute_url()


class TreeObjectRowsAction(objectpack.ObjectRowsAction):
    """
    Получение данных для древовидного списка объектов
    """

    def set_query(self):
        """
        выборка данных
        """
        super(TreeObjectRowsAction, self).set_query()
        # формирование предиката "лист"/"не лист"
        if hasattr(self.parent.model, 'is_leaf'):
            # модель может сама предоставлять признак "лист"/"не лист"
            self.is_leaf = lambda o: o.is_leaf
        else:
            # для моделей, не предоставляющих информацию о ветвлении,
            # формируется предикат на основе связей узлов дерева
            key = self.parent.parent_field
            parents = self.parent.model.objects.filter(**{
                ('%s__isnull' % key): False,
            }).values_list(
                '%s__id' % key,
                flat=True
            )
            self.is_leaf = lambda o: o.id not in parents

    def prepare_object(self, obj):
        """
        Сериализация объекта
        """
        data = super(TreeObjectRowsAction, self).prepare_object(obj)
        data['leaf'] = self.is_leaf(obj)
        return data

    def run(self, *args, **kwargs):
        result = super(TreeObjectRowsAction, self).run(*args, **kwargs)
        data = result.data.get('rows', [])
        return m3_actions.PreJsonResult(data)
