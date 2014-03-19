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

class NodesWindow(objectpack.BaseWindow):
    def _init_components(self):
        from m3_ext.ui import all_components as ext
        self.tree = ext.ExtTree()
        self.tree.add_column(header=u'Имя', data_index='name', width=140)
        self.tree.master_column_id = 'name'

        n = None
        first = None
        for i in (1, 2, 3):
            nn = ext.ExtTreeNode(text=unicode(i))
            nn.expanded = True
            if n:
                n.add_children(nn)
            n = nn
            first = first or n
        n.has_children = False
        n.can_check = True
        self.tree.nodes = [first]

    def _do_layout(self):
        self.items.append(self.tree)
        self.layout = 'fit'

    def set_params(self, params):
        super(NodesWindow, self).set_params(params)
