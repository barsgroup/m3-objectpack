# -*- coding: utf-8 -*-

import objectpack
import controller

import models


class GarageEditWindow(objectpack.TabbedEditWindow):
    """
    Окно редактирования
    """
    tabs = [
        objectpack.ObjectTab.fabricate(
            model=models.Garage, field_list=('name',)
        ),
        objectpack.ObjectGridTab.fabricate_from_pack(
            pack_name='objectpack.demo/StaffPack',
            pack_register=controller.obs,
        ),
        objectpack.ObjectGridTab.fabricate_from_pack(
            pack_name='objectpack.demo/ToolPack',
            pack_register=controller.obs
        ),
    ]
