#coding: utf-8
'''
File: app_meta.py
Author: Rinat F Sabitov
Description:
'''
from django.conf import urls

from m3_users import metaroles, GENERIC_USER
from objectpack import desktop

import actions
import controller



def register_urlpatterns():
    """
    Регистрация конфигурации урлов для приложения
    """
    return urls.defaults.patterns("",
        (r"^actions/", controller.action_controller.process_request))


def register_actions():
    """ регистрация экшенов"""
    controller.action_controller.packs.extend([
        actions.PersonObjectPack(),
        actions.BandedColumnPack(),
    ])


def register_desktop_menu():
    """
    регистрация элеметов рабочего стола
    """
    GENERIC_USER_METAROLE = metaroles.get_metarole(GENERIC_USER)
    desktop.uificate_the_controller(
        controller.action_controller,
        GENERIC_USER_METAROLE,
        menu_root=desktop.MainMenu.SubMenu(u'Демо-паки')
    )
