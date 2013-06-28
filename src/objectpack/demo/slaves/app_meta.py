# -*- coding: utf-8 -*-

from demo_app import controller

import actions


def register_actions():
    controller.action_controller.packs.extend([
        actions.GaragePack(),
        actions.ToolPack(),
        actions.StaffPack(),
    ])
