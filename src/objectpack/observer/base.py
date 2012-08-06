#coding:utf-8
'''
Created on 03.08.2012

@author: pirogov
'''
import re

from m3.ui import actions as m3_actions


class _BeforAfterPack:
    """
    Обертка для списка слушателей, реализующая вызов before/after
    в соответствии с приоритетом, определяемым порякрм слушателей
    """


    def __init__(self, listeners):
        self._listeners = listeners

    @staticmethod
    def lazy_chain(methods, *args):
        for m in methods:
            result = m(*args)
            if result:
                return result

    def _execute(self, verb, *args):
        # реакция слушателей на действие @verb=(before|after)
        for m in filter(None, (
                getattr(l(), verb, None)
                for l in self._listeners)):
            result = m(*args)
            if result:
                return result

    def pre_run(self, *args):
        return self._execute('before', *args)

    def post_run(self, *args):
        return self._execute('after', *args)


#===============================================================================
# ControllerMixin
#===============================================================================
class ControllerMixin(object):
    """
    Наблюдатель за вызовом actions и кода в точках их (actions) расшрения
    """

    def __init__(self, observer, *args, **kwargs):
        super(ControllerMixin, self).__init__(*args, **kwargs)
        self._observer = observer


    def _invoke(self, request, action, stack):
        """
        Вызов action под наблюдением
        """
        stack = stack[:]
        self._observer._prepare_for_listening(action, stack)

        # обработка контроллером
        return super(ControllerMixin, self)._invoke(request, action, stack)


    def append_pack(self, pack):
        """
        Добавление ActioPack`а с регистрацией его action`ов в ObserVer`е
        """
        super(ControllerMixin, self).append_pack(pack)
        self._observer._populate_pack(pack)


#===============================================================================
# ObservableController
#===============================================================================
class ObservableController(ControllerMixin, m3_actions.ActionController):
    """
    Контроллер, поддерживающий механизм подписки через Observer
    """
    pass


#===============================================================================
# Observer
#===============================================================================
class Observer(object):
    """
    Реестр слушателей, реализующий подписку последних на действия в actions
    """

    def __init__(self):
        self._registered_listeners = []
        self._action_listeners = {}
        self._actions = {}


    def _name_action(self, action):
        """
        Получение / генерация нового short_name для @action
        """
        def get_name(obj):
            name = getattr(obj, "short_name", None)
            if name and not isinstance(name, basestring):
                raise ValueError(
                    "The short_name must be a string! (%s)" % obj)
            return name

        short_name = get_name(action)
        if not short_name:
            # если у action нет short_name, генерируется новое имя по умолчанию
            cls_name = lambda obj: obj.__class__.__name__.lower()
            pack_name = get_name(action.parent) or cls_name(action.parent)
            action_name = get_name(action) or cls_name(action)
            short_name = '%s/%s' % (pack_name, action_name)
            # short_name проставляется в экземпляр action
            action.short_name = short_name

        return short_name


    def _reconfigure(self):
        """
        Перестройка дерева сопоставления экшнов со слушателями
        """
        self._action_listeners = {}
        # слушатели сортируются по приоритету
        listeners = [l[1] for l in
            sorted(self._registered_listeners, key=lambda x: x[0])]
        # зарегистрированные actions получают подписчиков
        for name in self._actions:
            action_listeners = []
            for is_listen, listener in listeners:
                if is_listen(name):
                    action_listeners.append(listener)
            self._action_listeners[name] = action_listeners


    def _populate_pack(self, pack):
        """
        Подписка зарегистрированных слушателей на @pack.actions 
        """
        for action in pack.actions:
            self._actions[self._name_action(action)] = action
        self._reconfigure()


    def subscribe(self, listener, priority=None):
        """
        Декоратор, регистрирующий слушателя @listener в реестре слушателей
        """
        priority = getattr(listener, 'priority', priority) or 0

        # matcher`ы по списку рег.выр. в параметре "from" слушателя 
        matchers = map(
            lambda p: re.compile(p).match,
            getattr(listener, 'listen', []))
        if matchers:
            is_listen = lambda name: any(m(name) for m in matchers)
        else:
            # если from не указан - слушатель слушает всех 
            is_listen = lambda name: True

        self._registered_listeners.append(
            (priority, (is_listen, listener))
        )
        self._reconfigure()

        return listener


    @staticmethod
    def _make_handlers(listeners):
        """
        Генератор методов, инжектируемых в action
        """
        def handle(verb, arg):
            """
            Обработка данных подписанными слушателями
            """
            for listener_cls in (l[1] for l in listeners):
                handler = getattr(listener_cls(), verb, None)
                if handler:
                    arg = handler(arg)
            return arg

        def handler_for(verb):
            """
            Декоратор для обертки пользовательской функции
            обработчиком на стороне слушателей
            """
            def wrapper(fn):
                def inner(*args, **kwargs):
                    return handle(verb, fn(*args, **kwargs))
            return wrapper

        return handle, handler_for


    def _prepare_for_listening(self, action, stack):
        """
        Подготовка action к прослушиванию (инжекция методов)
        """
        short_name = getattr(action, 'short_name', self._name_action(action))
        listeners = self._action_listeners.get(short_name, [])

        # в action инжектируются методы для работы подписки,
        # причем инжектирование производится и в случае,
        # когда подписчиков нет - для консистентности
        action.handle, action.handler_for = self._make_handlers(listeners)

        # если подписчики есть, в стек паков добавляется "пак",
        # реализующий подписку на before/after
        if listeners:
            stack.insert(0, _BeforAfterPack(listeners))
