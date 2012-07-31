#coding: utf-8

'''
File: context_processors.py
Author: Me
Description:
'''
from m3.ui.app_ui import DesktopModel, DesktopLoader
from m3.ui.actions import ControllerCache

def desktop(request):
    """
    добавляем элементы рабочего стола в контекст
    """

    desktop_items = DesktopModel()
    #этот костыль повзаимствован из образования
    #позволяет перестраивать рабочий стол для кажого нового пользователя
    #ControllerCache.populate()
    ControllerCache.populate()
    DesktopLoader._success = False
    #DesktopLoader.populate(request.user, desktop_items)
    DesktopLoader.populate(request.user, desktop_items, lambda x: (x.index, x.name))
    return {'components':desktop_items}

