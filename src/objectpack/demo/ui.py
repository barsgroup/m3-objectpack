# coding: utf-8
from m3_ext.ui.fields.complex import ExtMultiSelectField
from objectpack.ui import ObjectGridTab
from objectpack.ui import ObjectTab
from objectpack.ui import TabbedEditWindow

from . import controller
from . import models


class GarageTab(ObjectTab.fabricate(
        model=models.Garage, field_list=('name',))):

    def init_components(self, *args, **kwargs):
        super(GarageTab, self).init_components(*args, **kwargs)

        self._staff_field = ExtMultiSelectField(
            label=u'Сотрудники (пример поля множественного выбора)')
        self._controls.append(self._staff_field)

    def set_params(self, *args, **kwargs):
        super(GarageTab, self).set_params(*args, **kwargs)
        self._staff_field.pack = 'objectpack.demo.actions.StaffPack'
        self._staff_field.display_field = '__unicode__'


class GarageEditWindow(TabbedEditWindow):
    """
    Окно редактирования
    """
    tabs = [
        GarageTab,
        ObjectGridTab.fabricate_from_pack(
            pack_name='objectpack.demo.actions.StaffPack',
            pack_register=controller.obs,
        ),
        ObjectGridTab.fabricate_from_pack(
            pack_name='objectpack.demo.actions.ToolPack',
            pack_register=controller.obs
        ),
    ]
