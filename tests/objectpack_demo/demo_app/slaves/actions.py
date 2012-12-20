# -*- coding: utf-8 -*-

import objectpack

from m3.ui import actions as m3_actions

import models
import ui


#-----------------------------------------------------------------------------
class GaragePack(objectpack.ObjectPack):
    """
    Гаражи
    """
    model = models.Garage

    add_to_menu = True
    add_to_desktop = True

    add_window = objectpack.ModelEditWindow.fabricate(model)
    edit_window = ui.GarageEditWindow


#-----------------------------------------------------------------------------
class ToolPack(objectpack.SlavePack):
    """
    Инвентарь гаража
    """
    model = models.GarageTool

    parents = ['garage']

    add_window = edit_window = objectpack.ModelEditWindow.fabricate(
        model=model, field_list=('name',)
    )

    def configure_grid(self, grid):
        super(ToolPack, self).configure_grid(grid)
        grid.template = 'object-grid-w-param.js'
        grid.session_key_value = 123123
        grid.session_key_name = '%s_session_key' % self.short_name


#-----------------------------------------------------------------------------
class StaffPack(objectpack.SlavePack):
    """
    Сотрудники гаража
    """
    model = models.GarageStaff

    parents = ['garage']

    can_delete = True

    def __init__(self):
        super(StaffPack, self).__init__()

        self.save_staff_action = SaveStaffAction()
        self.select_person_action = SelectPersonAction()

        self.replace_action('new_window_action', self.select_person_action)
        self.actions.append(self.save_staff_action)


class SelectPersonAction(objectpack.SelectorWindowAction):
    """
    Экшн отображения списка физ.лиц
    """
    def configure_action(self, request, context):
        self.callback_url = self.parent.save_staff_action.get_absolute_url()
        self.data_pack = self.parent._get_model_pack('Person')


class SaveStaffAction(objectpack.BaseAction):
    """
    Экшн прикрепления физ.лиц к гаражу
    """
    url = r'/save_staff$'

    def run(self, request, context):
        ids = objectpack.extract_int_list(request, 'id')
        for i in ids:
            obj = models.GarageStaff(person_id=i)
            self.parent.save_row(obj, True, request, context)
        return m3_actions.OperationResult()
