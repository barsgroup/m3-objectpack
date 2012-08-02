#coding: utf-8
'''
File: app_meta.py
Author: Rinat F Sabitov
Description:
'''
from django.conf import urls
from objectpack_demo.demo_app.controller import action_controller
from m3_users import metaroles, GENERIC_USER
import actions


from objectpack import desktop


def register_urlpatterns():
    """
    Регистрация конфигурации урлов для приложения
    """
    return urls.defaults.patterns("",
        (r"^actions/", action_controller.process_request))

def register_actions():
    """ регистрация экшенов"""
    action_controller.packs.append(actions.PersonObjectPack())

def register_desktop_menu():
    """
    регистрация элеметов рабочего стола
    """
    GENERIC_USER_METAROLE = metaroles.get_metarole(GENERIC_USER)
    desktop.uificate_the_controller(
        action_controller,
        GENERIC_USER_METAROLE,
        menu_root=desktop.MainMenu.TO_REGISTRIES)
