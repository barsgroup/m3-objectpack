# -*- coding: utf-8 -*-

import objectpack
from m3_ext.ui import all_components as ext

from . import controller
from . import models


class GarageTab(objectpack.ObjectTab.fabricate(
        model=models.Garage, field_list=('name',))):

    def init_components(self, *args, **kwargs):
        super(GarageTab, self).init_components(*args, **kwargs)
        self._staff_field = ext.ExtMultiSelectField(
            label=u'Сотрудники (пример поля множественного выбора)')
        self._controls.append(self._staff_field)

    def set_params(self, *args, **kwargs):
        super(GarageTab, self).set_params(*args, **kwargs)
        self._staff_field.pack = 'objectpack.op_demo.actions.StaffPack'
        self._staff_field.display_field = '__unicode__'


class GarageEditWindow(objectpack.TabbedEditWindow):
    """
    Окно редактирования
    """
    tabs = [
        GarageTab,
        objectpack.ObjectGridTab.fabricate_from_pack(
            pack_name='objectpack.op_demo/StaffPack',
            pack_register=controller.obs,
        ),
        objectpack.ObjectGridTab.fabricate_from_pack(
            pack_name='objectpack.op_demo/ToolPack',
            pack_register=controller.obs
        ),
    ]


class PersonCardEditWindow(objectpack.ModelEditWindow):
    """
    Окно редактирования карточки физ-лица
    """
    model = models.PersonCard

    field_fabric_params = {
        'exclude_list': [
            '*_id'
        ]
    }
