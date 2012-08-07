#coding:utf-8
'''
Created on 03.08.2012

@author: pirogov
'''
import re

from m3.ui import actions as m3_actions


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
    # уровни детализации отладочного логировния
    LOG_NONE, LOG_CALLS, LOG_MORE = 0, 1, 2


    class _BeforAfterPack:
        """
        Обертка для списка слушателей, реализующая вызов before/after
        в соответствии с приоритетом, определяемым порякрм слушателей
        """

        def __init__(self, action, listeners, logger):
            self._listeners = listeners
            self._action = action
            self._logger = logger

        @staticmethod
        def lazy_chain(methods, *args):
            for m in methods:
                result = m(*args)
                if result:
                    return result

        def _execute(self, verb, *args):
            # реакция слушателей на действие @verb=(before|after)
            for listener in self._listeners:
                # слушатель должен иметь метод с именем из verb
                method = getattr(listener, verb, None)
                if method:
                    # слушатель инстанцируется каждый раз
                    listener = listener()
                    # инжекция action в слушателя
                    listener.action = self._action
                    # вызывается метод слушателя для нового экземпляра слушателя
                    result = method(listener, *args)
                    if result:
                        return result

        def pre_run(self, *args):
            return self._execute('before', *args)

        def post_run(self, *args):
            return self._execute('after', *args)


    def __init__(self, logger=lambda msg: None, verbose_level=None):
        """
        Создание наблюдателя.
        @logger - метод логирования: callable-объект,
            вызываемый для каждого сообщения (параметр - текст сообщения)
        @verbose_level - уровень подробности логирования:
            одна из констант Observer.LOG_xxx
        """
        self._logger = logger
        self._verbose_level = verbose_level

        self._registered_listeners = []
        self._action_listeners = {}
        self._actions = {}


    def _log(self, level, message):
        """
        Логирование действий с проверкой уровня подробности
        """
        if self._verbose_level >= level:
            self._logger(message)


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

            self._log(self.LOG_MORE,
                'short_name gererated:\n\tAction\t\t %r\n\tshort_name\t "%s"'
                % (action, short_name))

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
                    self._log(self.LOG_MORE,
                        'Action linked:\n\tshort_name\t "%s"'
                        '\n\tListener\t %r' % (name, listener))
            self._action_listeners[name] = action_listeners


    def _populate_pack(self, pack):
        """
        Подписка зарегистрированных слушателей на @pack.actions 
        """
        for action in pack.actions:
            short_name = self._name_action(action)
            # возбуждение исключения при коллизии short_names
            if short_name in self._actions:
                raise AssertionError(
                    'Action %r have short_name="%s", '
                    ' already registered with vs %r!'
                    % (action, short_name, self._actions[short_name]))
            self._actions[short_name] = action
        self._reconfigure()


    def subscribe(self, listener):
        """
        Декоратор, регистрирующий слушателя @listener в реестре слушателей
        """
        priority = getattr(listener, 'priority', 0) or 0

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
        self._log(self.LOG_MORE,
            'Listener registered:\n\tListener %r' % listener)

        self._reconfigure()

        return listener


    def _configure_action(self, action, listeners):
        """
        Конфигурирует @action, инжектируя в него методы handle и handler_for,
        взаимрдействующие со слушателями @listeners
        """
        def handle(verb, arg):
            """
            Обработка данных @arg подписанными слушателями, которые имеют
            обработчик @verb
            """
            for listener in listeners:
                handler = getattr(listener, verb, None)
                if handler:
                    self._log(self.LOG_CALLS,
                        'Listener call:\n\t'
                        'Action\t %r\n\tListener %r\n\tVerb\t "%s"' %
                        (action, listener, verb))
                    # слушатель инстанцируется каждый раз
                    listener = listener()
                    # инжекция action в слушателя
                    listener.action = action
                    # вызывается метод слушателя для нового экземпляра слушателя
                    arg = handler(listener, arg)
            return arg

        def handler_for(verb):
            """
            Декоратор для обертки пользовательской функции
            обработчиком (с именем @verb) на стороне слушателей
            """
            def wrapper(fn):
                def inner(*args, **kwargs):
                    return handle(verb, fn(*args, **kwargs))
            return wrapper

        action.handle = handle
        action.handler_for = handler_for


    def _prepare_for_listening(self, action, stack):
        """
        Подготовка action к прослушиванию (инжекция методов)
        """
        short_name = getattr(action, 'short_name', self._name_action(action))
        listeners = self._action_listeners.get(short_name, [])

        # в action инжектируются методы для работы подписки,
        # причем инжектирование производится и в случае,
        # когда подписчиков нет - для консистентности
        self._configure_action(action, listeners)

        # если подписчики есть, в стек паков добавляется "пак",
        # реализующий подписку на before/after
        if listeners:
            stack.insert(0, self._BeforAfterPack(
                action, listeners,
                # инжекция логирования
                logger=lambda msg: self._log(self.LOG_CALLS, msg)
            ))
