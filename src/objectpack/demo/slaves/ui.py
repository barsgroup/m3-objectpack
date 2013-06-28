# -*- coding: utf-8 -*-

import objectpack
from demo_app import controller

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
            pack_name='demo_app.slaves/StaffPack',
            pack_register=controller.obs,
        ),
        objectpack.ObjectGridTab.fabricate_from_pack(
            pack_name='demo_app.slaves/ToolPack',
            pack_register=controller.obs
        ),
    ]
