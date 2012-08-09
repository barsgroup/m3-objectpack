#coding:utf-8
'''
Created on 03.08.2012

@author: pirogov
'''
import re
import inspect

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


    @property
    def urlpattern(self):
        """
        Возвращает кортеж вида (pattern, method), пригодный для регистрации
        в urlpatterns Django
        """
        url = self.url
        if url.startswith('/'):
            url = url[1:]
        if url.endswith('/'):
            url = url[:-2]
        return (r'^%s/' % url, self.process_request)


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
                    # логирование
                    self._logger(
                        'Listener call:\n\t'
                        'Action\t %r\n\tListener %r\n\tVerb\t "%s"' %
                        (self._action, listener, verb))
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

        self._model_register = {}


    def get(self, model_name):
        """
        Поиск экземпляра ActionPack для модели по имени её класса.
        Поиск производится среди зарегистрированных Pack`ов, которые являются
        основными для своих моделей (и привязаны к модели)
        """
        return self._model_register.get(model_name)


    def _log(self, level, message):
        """
        Логирование действий с проверкой уровня подробности
        """
        if self._verbose_level >= level:
            self._logger(message)


    def _name_action(self, action):
        """
        Получение / генерация полного имени для @action
        """
        name = getattr(action, '_observing_name', None)
        if not name:
            pack_cls = action.parent.__class__
            # имя подписки будет иметь вид "пакет/КлассПака/КлассAction"
            name = '%s/%s/%s' % (
                inspect.getmodule(pack_cls).__package__,
                pack_cls.__name__,
                action.__class__.__name__,
            )
            # название подписки проставляется в экземпляр action
            action._observing_name = name

            self._log(self.LOG_MORE,
                'Name gererated:\n\tAction\t %r\n\tname\t "%s"'
                % (action, name))

        return name


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
        # регистрация ActionPack, как основного для модели
        try:
            if pack._is_primary_for_model and pack.model:
                model_name = pack.model.__name__
                try:
                    # если для модели уже зарегистрирован ActionPack
                    # возбуждается исключение
                    raise AssertionError(
                        "For model %s already registered primary pack: %r"
                        % (model_name, self._model_register[model_name]))
                except KeyError:
                    # модель ещё не регистрировалась - регистрируется
                    self._model_register[model_name] = pack
        except AttributeError:
            # Если Pack не основной, или не имеет модели - игнорируется
            pass

        for action in pack.actions:
            name = self._name_action(action)
            # возбуждение исключения при коллизии short_names
            if name in self._actions:
                raise AssertionError(
                    'Name="%s" can not be registered for action %r,\n'
                    'because this name ristered for %r!'
                    % (action, name, self._actions[name]))
            self._actions[name] = action
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
        listeners = self._action_listeners.get(self._name_action(action), [])

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
