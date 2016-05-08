# coding: utf-8
from django.conf.urls import patterns
from objectpack import desktop

from . import actions
from . import controller


def register_urlpatterns():
    """
    Регистрация конфигурации урлов для приложения
    """
    return patterns(
        "",
        controller.action_controller.urlpattern
    )


def register_actions():
    """
    регистрация экшенов
    """
    controller.action_controller.packs.extend([
        actions.PersonObjectPack(),
        actions.CFPersonObjectPack(),
        actions.BandedColumnPack(),
        actions.TreePack(),

        actions.GaragePack(),
        actions.ToolPack(),
        actions.StaffPack(),

        actions.ROStaffPack(),
    ])


def register_desktop_menu():
    """
    регистрация элеметов рабочего стола
    """
    desktop.uificate_the_controller(
        controller.action_controller,
        menu_root=desktop.MainMenu.SubMenu(u'Демо-паки')
    )
