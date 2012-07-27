#coding:utf-8
'''
Created on 23.07.2012

@author: pirogov
'''
from m3.ui import app_ui, actions


#===============================================================================
# uificate_the_controller
#===============================================================================
def uificate_the_controller(controller, metarole):
    '''
    Интеграция в интерфейс рабочего стола паков контроллера
    '''
    for pack in controller.top_level_packs:
        Desktop.from_pack(pack, for_metarole=metarole)
        MainMenu.from_pack(pack, for_metarole=metarole)

#===============================================================================
def _add_to(metarole, to_, items):
    #if _users.metaroles.get_metarole(metarole)
    for item in items:
        app_ui.DesktopLoader.add(metarole, to_, item)

def _add_to_desktop(metarole, *items):
    '''
    Добавление элементов на Рабочий Стол
    '''
    _add_to(metarole, app_ui.DesktopLoader.DESKTOP, items)

def _add_to_toolbox(metarole, *items):
    '''
    Добавление элементов в меню инструментов (справа в главном меню)
    '''
    _add_to(metarole, app_ui.DesktopLoader.TOOLBOX, items)

def _add_to_menu(metarole, *items):
    '''
    Добавление элементов в главное меню
    '''
    _add_to(metarole, app_ui.DesktopLoader.START_MENU, items)


#===============================================================================
# DesktopItem
#===============================================================================
class DesktopItem(app_ui.DesktopShortcut):
    '''
    Элемент UI с запоминанием кода права
    '''
    def __init__(self, pack, *args, **kwargs):
        is_pack = isinstance(pack, actions.ActionPack)
        is_action = isinstance(pack, actions.Action)
        if not (is_pack or is_action):
            raise TypeError(u'pack must be instance of Action/ActionPack!')

        need = lambda obj: getattr(obj, 'need_check_permission', False)
        if is_action:
            if need(pack) and need(pack.parent):
                code = pack.get_permission_code()
            else:
                code = None
        else:
            try:
                action = pack.get_default_action()
                if not isinstance(action, actions.Action):
                    raise AttributeError()
                if need(action) and need(action.parent):
                    code = action.get_permission_code()
                else:
                    code = None
                pack = action
            except AttributeError:
                raise AttributeError(
                    u'Pack must provide "get_default_action" method,'
                    u' returning action instance!'
                )
        self.permission_code = code
        return super(DesktopItem, self).__init__(pack, *args, **kwargs)


#===============================================================================
# _UIFabric
#===============================================================================
class _UIFabric(object):
    '''
    Прототип построителя UI
    '''
    pack_method = ''


    class LauncherItem(object):
        '''
        Элемент меню
        '''
        def __init__(self, name, **kwargs):
            self._args = kwargs
            self._args['name'] = name

        def _populate(self):
            return app_ui.DesktopLauncher(**self._args)


    class Item(object):
        '''
        Элемент меню для пака/экшна
        '''
        def __init__(self, name, pack, **kwargs):
            self._args = kwargs
            self._args['name'] = name
            self._args['pack'] = pack

        def _populate(self):
            return DesktopItem(**self._args)


    def _populate(self, data):
        #Делаем данные всегда итерируемыми
        try:
            data = list(data)
        except TypeError:
            data = [data]
        return map(lambda o: o._populate(), filter(None, data))


    @classmethod
    def from_pack(cls, pack, for_metarole):
        '''
        Расширение UI из пака
        '''
        ui_fabric = cls()
        method = getattr(pack, cls.pack_method, None)
        if callable(method):
            data = method(ui_fabric)
        else:
            data = ui_fabric._from_dict_pack(pack)
        if data:
            ui_fabric._populate(for_metarole, data)


    def _from_dict_pack(self):
        '''
        Расширение UI из пака справочника
        '''
        # нужно реализовать в потомке
        raise NotImplementedError()


#===============================================================================
# MainMenu
#===============================================================================
class MainMenu(_UIFabric):
    '''
    Класс для работы с главным меню
    '''
    pack_method = 'extend_menu'


    class SubMenu(object):
        '''
        Подменю
        '''
        def __init__(self, name, *items, **kwargs):
            self._args = a = {}
            a.update(kwargs)
            a['name'] = name

            self._items = items or []

        def _populate(self):
            items = map(lambda o: o._populate(), filter(None, self._items))
            if items:
                grp = app_ui.DesktopLaunchGroup(**self._args)
                grp.subitems.extend(items)
                return grp
            return None


    def __init__(self):
        self._registries_menu = self.SubMenu(
            u'Реестры', icon='menu-dicts-16', index=1)
        self._dicts_menu = self.SubMenu(
            u'Справочники', icon='menu-dicts-16', index=2)
        self._administry_menu = self.SubMenu(
            u'Администрирование', icon='menu-dicts-16', index=101)


    def dicts(self, *items):
        '''
        Добавление элементов в меню "Справочники"
        '''
        self._dicts_menu._items.extend(items)
        return self._dicts_menu


    def registries(self, *items):
        '''
        Добавление элементов в меню "Реестры"
        '''
        self._registries_menu._items.extend(items)
        return self._registries_menu


    def administry(self, *items):
        '''
        Элементы для меню "администрирование"
        '''
        self._administry_menu._items.extend(items)
        return self._administry_menu


    def _populate(self, metarole, data):
        '''
        Построение интерфейса
        '''
        _add_to_menu(metarole, *super(MainMenu, self)._populate(data))


    def _from_dict_pack(self, pack):
        try:
            assert pack.title
            if getattr(pack, 'add_to_menu', False):
                return self.Item(name=pack.title, pack=pack)
            else:
                return None
        except (AttributeError, AssertionError):
            return None


#===============================================================================
# Desktop
#===============================================================================
class Desktop(_UIFabric):
    '''
    Класс для работы с Рабочим Столом
    '''
    pack_method = 'extend_desktop'

    def _populate(self, metarole, data):
        '''
        Построение интерфейса
        '''
        _add_to_desktop(metarole, *super(Desktop, self)._populate(data))

    def _from_dict_pack(self, pack):
        try:
            assert pack.title
            if getattr(pack, 'add_to_desktop', False):
                return self.Item(name=pack.title, pack=pack)
            else:
                return None
        except (AttributeError, AssertionError):
            return None
