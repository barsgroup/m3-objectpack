#coding: utf-8
"""
Created on 23.07.2012

@author: pirogov
"""

import copy
import datetime
import re
import inspect
import types
import json

from django.db import models
from django.db.models import fields as dj_fields
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _
from django.utils import simplejson

from m3.ui import actions as m3_actions
from m3.ui.actions.interfaces import ISelectablePack
from m3.ui.ext.fields.complex import ExtSearchField
from m3.core.exceptions import RelatedError, ApplicationLogicException
from m3.db import safe_delete

import ui
import tools
import exceptions


#==============================================================================
# BaseAction
#==============================================================================
class BaseAction(m3_actions.Action):
    """
    Прототип для actions ObjectPack`а
    """
    # код подправа, используемый при формировании кода права экшна
    # стандартным способом. Если код не указан - экшн формирует
    # свой код права независимо от пака
    perm_code = None

    @property
    def url(self):
        # автоматически генерируемый url
        return r'/%s' % self.__class__.__name__.lower()

    def get_perm_code(self, subpermission=None):
        if self.perm_code is None:
            code = super(BaseAction, self).get_perm_code(subpermission)
        else:
            perm_code = self.perm_code + (
                ('/' + subpermission) if subpermission else ''
            )
            code = self.parent.get_perm_code(perm_code)
        return code

    @property
    def need_check_permission(self):
        # Если определен perm_code, то необходимость проверки прав
        # будет зависеть от присутствия perm_code среди sub_permissions пака
        # и соответствующего флага пака
        if self.perm_code is not None:
            result = (
                self.parent.need_check_permission
                and
                self.perm_code in self.parent.sub_permissions
            )
        else:
            result = False
        return result

    @staticmethod
    def handle(verb, arg):
        """
        Заглушка для точек расширения.
        При регистрации в обсервер перекрывается
        """
        return arg

    @staticmethod
    def handler_for(verb):
        """
        Декоратор-заглушка для точек расширения.
        При регистрации в обсервер перекрывается
        """
        def wrapper(fn):
            return fn
        return wrapper


#==============================================================================
# BaseWindowAction
#==============================================================================
class BaseWindowAction(BaseAction):
    """
    Базовый Action показа окна
    """
    def create_window(self):
        """
        Метод инстанцирует окно и помещает экземпляр в атрибут self.win
        ( пример: self.win = EditWindow() )
        """
        raise NotImplementedError()

    def set_windows_params(self):
        # TODO: Выпилить, ато опечатка портит всю семантику!
        self.set_window_params()

    def _apply_windows_params(self):
        # TODO: Выпилить, ато опечатка портит всю семантику!
        self._apply_window_params()

    def set_window_params(self):
        """
        Метод заполняет словарь self.win_params, который будет передан
        в окно. Этот словарь выступает как шина передачи данных
        от Actions/Packs к окну.
        ( пример: self.win_params['title'] = _(u'Привет из ада') )
        """
        pass

    def _apply_window_params(self):
        """
        Метод передает словарь параметров в окно.
        ( Обычно не требует перекрытия )
        """
        self.win.set_params(self.win_params)

    def configure_window(self):
        """
        Точка расширения, предоставляющая доступ к настроенному
        экземпляру окна для тонкой настройки.
        ( Оставлена для особо тяжёлых случаев,
        когда не удаётся обойтись set_params )
        ( пример: self.win.grid.top_bar.items[8].text = _(u'Ух ты, 9 кнопок') )
        """
        pass

    def run(self, request, context):
        """
        Тело Action, вызывается при обработке запроса к серверу.
        ( обычно не требует перекрытия )
        """
        new_self = copy.copy(self)
        new_self.win_params = (
            getattr(self.__class__, 'win_params', None) or {}
        ).copy()
        new_self.request = request
        new_self.context = context
        new_self.set_window_params()
        new_self.create_window()
        new_self._apply_window_params()
        new_self.configure_window()
        return m3_actions.ExtUIScriptResult(
            new_self.win, context=new_self.context)


#==============================================================================
# ObjectListWindowAction
#==============================================================================
class ObjectListWindowAction(BaseWindowAction):
    """
    Базовый Action показа окна списка объектов.
    """
    is_select_mode = False  # режим показа окна (True - выбор, False - список)

    perm_code = 'view'

    def set_window_params(self):
        params = self.win_params
        params['is_select_mode'] = self.is_select_mode
        params['pack'] = self.parent
        params['title'] = self.parent.title
        params['height'] = self.parent.height
        params['width'] = self.parent.width
        params['read_only'] = getattr(self.parent, 'read_only', None) or (
            not self.has_perm(self.request))

        self.win_params = self.parent.get_list_window_params(
            params, self.request, self.context)

    def create_window(self):
        self.win = self.parent.create_list_window(
            is_select_mode=self.win_params['is_select_mode'],
            request=self.request,
            context=self.context)


#==============================================================================
# ObjectSelectWindowAction
#==============================================================================
class ObjectSelectWindowAction(ObjectListWindowAction):
    """
    Базовый Action показа окна списка выбора объекта из списка.
    """
    is_select_mode = True

    def set_window_params(self):
        super(ObjectSelectWindowAction, self).set_window_params()
        # В окне выбора можно только ВЫБИРАТЬ!
        self.win_params['read_only'] = True
        self.win_params['column_name_on_select'] = (
            self.parent.column_name_on_select)


#==============================================================================
# ObjectEditWindowAction
#==============================================================================
class ObjectEditWindowAction(BaseWindowAction):
    """
    Базовый Action показа окна редактирования объекта.
    """
    perm_code = 'edit'

    def set_window_params(self):
        try:
            obj, create_new = self.parent.get_obj(self.request, self.context)
        except self.parent.get_not_found_exception():
            raise ApplicationLogicException(self.parent.MSG_DOESNOTEXISTS)

        params = self.win_params.copy()
        params['object'] = obj
        params['create_new'] = create_new
        params['form_url'] = self.parent.save_action.get_absolute_url()

        read_only = getattr(self.parent, 'read_only', None) or (
            not self.has_perm(self.request))

        params['read_only'] = read_only
        params['title'] = self.parent.format_window_title(
            _(u'Просмотр') if read_only else
            _(u'Добавление') if create_new else
            _(u'Редактирование')
        )

        self.win_params = self.parent.get_edit_window_params(
            params, self.request, self.context)

    def create_window(self):
        assert 'create_new' in self.win_params, (
            u'You must call "set_window_params" method of superclass!')
        self.win = self.parent.create_edit_window(
            self.win_params['create_new'], self.request, self.context)


#==============================================================================
# ObjectAddWindowAction
#==============================================================================
class ObjectAddWindowAction(ObjectEditWindowAction):
    """
    Базовый Action показа окна добавления объекта.
    """
    perm_code = 'add'

    # Отдельный action для уникальности short_name
    pass


#==============================================================================
# ObjectSaveAction
#==============================================================================
class ObjectSaveAction(BaseAction):
    """
    Базовый Action сохранения отредактированного объекта.
    """
    class AlreadySaved(Exception):
        """
        Исключение, с помощью которого расширение,
        перекрывшее сохранение объекта,
        может сообщить, что объект сохранен
        и больше ничего делать не нужно.
        """
        pass

    def create_window(self):
        self.win = self.parent.create_edit_window(
            self.create_new, self.request, self.context)

    def create_obj(self):
        """
        Метод загружает из БД / создаёт новый объект модели.
        """
        try:
            self.obj, self.create_new = self.parent.get_obj(
                self.request, self.context)
        except self.parent.get_not_found_exception():
            raise ApplicationLogicException(
                self.parent.MSG_DOESNOTEXISTS)

    def bind_win(self):
        """
        Заполнение полей окна по данным из request.
        """
        self.win.form.bind_to_request(self.request)

    def bind_to_obj(self):
        """
        Заполнение объекта данными из полей окна.
        """
        self.win.form.to_object(self.obj)

    def save_obj(self):
        """
        Сохранение объекта в БД
        """
        # инжекция классов исключений в объект
        self.obj.AlreadySaved = self.AlreadySaved
        try:
            try:
                self.obj = self.handle('save_object', self.obj)
            except self.AlreadySaved:
                # кто-то в цепочке слушателей обработал сохранение объекта
                # и больше ничего делать не нужно
                return
            self.parent.save_row(
                self.obj, self.create_new, self.request, self.context)
        except (exceptions.ValidationError, exceptions.OverlapError) as err:
            raise ApplicationLogicException(unicode(err))

    def run(self, request, context):
        """
        Тело Action, вызывается при обработке запроса к серверу.
        ( обычно не требует перекрытия )
        """
        new_self = copy.copy(self)
        new_self.request = request
        new_self.context = context
        new_self.create_obj()
        new_self.create_window()
        new_self.bind_win()
        new_self.bind_to_obj()
        new_self.save_obj()
        return m3_actions.OperationResult()


#==============================================================================
# ObjectRowsAction
#==============================================================================
class ObjectRowsAction(BaseAction):
    """
    Базовый Action получения данных для отображения в окне списка объектов.
    """
    def set_query(self):
        """
        Метод получает первоначальную выборку данных в виде QuerySet
        и помещает в атрибут self.query
        """
        self.query = self.handle(
            'query',
            self.parent.get_rows_query(self.request, self.context)
        )

    def apply_search(self):
        """
        Метод применяет к выборке self.query фильтр по тексту
        из поля "Поиск" окна списка.
        """
        self.query = self.handle(
            'apply_search',
            self.parent.apply_search(
                self.query,
                self.request,
                self.context
            ))

    def apply_filter(self):
        """
        Метод применяет к выборке self.query фильтр, как правило поступающий
        от "колоночных фильтров"/фильтров в контекстных меню в окне списка.
        """
        self.query = self.handle(
            'apply_filter',
            self.parent.apply_filter(
                self.query,
                self.request,
                self.context
            ))

    def apply_sort_order(self):
        """
        Метод применяет к выборке self.query сортировку
        по выбранному в окне списка столбцу.
        """
        self.query = self.handle(
            'apply_sort_order',
            self.parent.apply_sort_order(
                self.query,
                self.request,
                self.context
            ))

    def apply_limit(self):
        """
        Метод применяет к выборке self.query операцию оганичения
        по количеству элементов (для порционной загрузки в окно списка).
        """
        if getattr(self.parent, 'allow_paging', True):
            offset = m3_actions.utils.extract_int(self.request, 'start')
            limit = m3_actions.utils.extract_int(self.request, 'limit')
        else:
            offset = limit = 0
        self.query = tools.QuerySplitter(self.query, offset, limit)

    def get_rows(self):
        """
        Метод производит преобразование QuerySet в список.
        При этом объекты сериализуются в словари.
        """
        res = []
        for obj in self.query:
            prep_obj = self.prepare_object(obj)
            if prep_obj:
                res.append(prep_obj)
            else:
                self.query.skip_last()
        return self.handle('get_rows', res)

    def prepare_object(self, obj):
        """
        Возвращает словарь, для составления результирующего списка.
        @obj - объект, полученный из QuerySet'a
        """
        if hasattr(self.parent, 'prepare_row'):
            obj = self.parent.prepare_row(obj, self.request, self.context)
        if obj is None:
            return None

        result_dict = {}

        def parse_data_indexes(obj, col, result):
            # сплит строки вида "asdad[.asdasd]" на "голову" и "хвост"
            # "aaa" -> "aaa", None
            # "aaa.bbb.ccc" -> "aaa", "bbb.ccc"
            col, subcol = (col.split('.', 1) + [None])[:2]
            # ------- если есть подиндекс - идем вглубь
            if subcol:
                obj = getattr(obj, col, None)
                sub_dict = result.setdefault(col, {})
                parse_data_indexes(obj, subcol, sub_dict)
            else:
                # --- подиндекса нет - получаем значение
                # ищем поле в модели
                try:
                    fld = obj._meta.get_field_by_name(col)[0]
                except AttributeError:
                    fld = None
                except IndexError:
                    fld = None
                except dj_fields.FieldDoesNotExist:
                    fld = None
                # получаем значение
                obj = getattr(obj, col, None)
                if fld:
                    try:
                        obj = obj.display()
                    except AttributeError:
                        if fld.choices:
                            # если получаемый атрибут - поле, имеющее choices
                            # пробуем найти соответствующий значению вариант
                            for ch in fld.choices:
                                if obj == ch[0]:
                                    obj = ch[1]
                                    break
                            else:
                                obj = u''

                else:
                    # атрибут (не поле) может быть вызываемым
                    if callable(obj):
                        obj = obj()

                if isinstance(obj, datetime.datetime):
                    obj = obj.strftime('%d.%m.%Y %H:%M:%S')
                elif isinstance(obj, datetime.date):
                    obj = obj.strftime('%d.%m.%Y')

                if obj is None:
                    # None выводится пустой строкой
                    obj = u''

                if not isinstance(obj, (int, bool)):
                    obj = force_unicode(obj)
                result[col] = obj

        #заполним объект данными по дата индексам
        for col in self.get_column_data_indexes():
            parse_data_indexes(obj, col, result_dict)

        return self.handle('prepare_obj', result_dict)

    def get_total_count(self):
        """
        Возвращает общее кол-во объектов
        """
        return self.query.count()

    def get_column_data_indexes(self):
        """
        Возвращает список data_index колонок, для формирования json
        """
        res = ['__unicode__', ]
        for col in getattr(self.parent, '_columns_flat', []):
            res.append(col['data_index'])
        res.append(self.parent.id_field)
        return res

    def handle_row_editing(self, request, context, data):
        """
        Обрабатывает inline-редактирования грида.
        Метод должен вернуть пару вида (удачно/неудачно, "сообщение"/None)
        """
        return self.handle(
            'row_editing',
            self.parent.handle_row_editing(request, context, data)
        )

    def run(self, request, context):
        new_self = copy.copy(self)
        new_self.request = request
        new_self.context = context

        if request.REQUEST.get('xaction') not in ['read', None]:
            data = json.loads(request.REQUEST.get('rows'))
            if not isinstance(data, list):
                data = [data]
            success, message = self.handle_row_editing(
                request=request,
                context=context,
                data=data)
            result = m3_actions.OperationResult(
                success=success, message=message)
        else:
            new_self.set_query()
            new_self.apply_search()
            new_self.apply_filter()
            new_self.apply_sort_order()
            total_count = new_self.get_total_count()
            new_self.apply_limit()
            rows = new_self.get_rows()
            result = m3_actions.PreJsonResult({
                'rows': rows,
                'total': total_count
            })
        return result


#==============================================================================
# ObjectDeleteAction
#==============================================================================
class ObjectDeleteAction(BaseAction):
    """
    Действие по удалению объекта
    """
    perm_code = 'delete'

    def try_delete_objs(self):
        """
        удаляет обекты и пытается перехватить исключения
        """
        # TODO: разгрести этот УЖАС!
        try:
            self.delete_objs()
        except RelatedError, e:
            raise ApplicationLogicException(e.args[0])
        except Exception, e:
            if e.__class__.__name__ == 'IntegrityError':
                message = _(
                    u'Не удалось удалить элемент. '
                    u'Возможно на него есть ссылки.')
                raise ApplicationLogicException(message)
            else:
                # все левые ошибки выпускаем наверх
                raise

    def delete_objs(self):
        """
        Удаляет обекты
        """
        ids = m3_actions.utils.extract_int_list(
            self.request, self.parent.id_param_name)
        for i in ids:
            self.delete_obj(i)

    def audit(self, obj):
        """
        Обработка успешно удалённых объектов
        """
        pass

    def delete_obj(self, id_):
        """
        Удаление объекта по идентификатору @id_
        """
        obj = self.parent.delete_row(id_, self.request, self.context)
        self.audit(obj)

    def run(self, request, context):
        new_self = copy.copy(self)
        new_self.request = request
        new_self.context = context
        new_self.try_delete_objs()
        return m3_actions.OperationResult()


#==============================================================================
# BasePack
#==============================================================================
class BasePack(m3_actions.ActionPack):
    """
    Потомок ActionPack, реализующий автогенерацию short_name, url
    """

    @classmethod
    def get_short_name(cls):
        """
        Имя пака для поиска в ControllerCache
        """
        name = cls.__dict__.get('_auto_short_name')
        if not name:
            name = '%s/%s' % (
                inspect.getmodule(cls).__name__.replace(
                    '.actions', ''
                ).replace(
                    '.', '/').lower(),
                cls.__name__.lower())
            cls._auto_short_name = name
        return name

    @property
    def short_name(self):
        # имя пака для поиска в ControllerCache в виде атрибута
        # для совместимости с m3
        return self.get_short_name()

    @property
    def url(self):
        return r'/%s' % self.short_name

    @classmethod
    def absolute_url(cls):
        # получение url для построения внутренних кэшей m3
        path = [r'/%s' % cls.get_short_name()]
        pack = cls.parent
        while pack is not None:
            path.append(pack.url)
            pack = pack.parent
        for cont in m3_actions.ControllerCache.get_controllers():
            p = cont.find_pack(cls)
            if p:
                path.append(cont.url)
                break
        return ''.join(reversed(path))


#==============================================================================
# ObjectPack
#==============================================================================
class ObjectPack(BasePack, ISelectablePack):
    """
    Пакет с действиями, специфичными для работы с редактирование модели
    """

    # Заголовок окна справочника
    # если не перекрыт в потомках - берется из модели
    @property
    def title(self):
        return unicode(
            self.model._meta.verbose_name_plural or
            self.model._meta.verbose_name or
            repr(self.model)).capitalize()

    # Список колонок

    # ВАЖНО: для корректной работы полей выбора,
    # необходима колонка с data_index = '__unicode__'
    columns = [
        {
            'header': _(u'Наименование'),
            'data_index': '__unicode__',
        },
#        {
#            'data_index':'',
#            'width':,
#            'header':u'',
#            'serchable':True,
#            'sortable':True,
#            'sort_fields': ('foo','bar'),
#        },
#        {
#            'header':u'Группирующая Колонка 1',
#            'columns': [
#                {
#                    'data_index':'school.name',
#                    'width':200,
#                    'header':u'Колонка 1',
#                    'searchable':True,
#                    'search_fields': ('school.fullname',),
#                },
#            ]
#        },
#        {
#            'data_index':'school.parent.name',
#            'width':200,
#            'header':u'Родитель',
#            'renderer':'parent_render'
#        },
    ]

    # Настройки вида справочника (задаются конечным разработчиком)
    model = None

    # название поля, идентифицирующего объект и название параметра,
    # который будет передаваться в запросе на модификацию/удаление
    @property
    def id_param_name(self):
        return '%s_id' % self.short_name

    # data_index колонки, идентифицирующей объект
    # этот параметр будет браться из модели и передаваться как ID
    # в ExtDataStore, т.е в post запросе редактирования будет
    # лежать { id_param_name:obj.id_field }
    id_field = 'id'

    # поле/метод, предоставляющее значение для отображения в DictSelectField
    # ПОКА НЕ РАБОТАЕТ извлечение вложенных полей - конфликт с ExtJS
    column_name_on_select = '__unicode__'

    # Список дополнительных полей модели по которым будет идти поиск
    # основной список береться из colums по признаку searchable
    search_fields = None
    allow_paging = True

    # пак будет настраивать грид на возможность редактирования
    read_only = False

    # Порядок сортировки элементов списка. Работает следующим образом:
    # 1. Если в list_columns модели списка есть поле
    # code, то устанавливается сортировка по
    # возрастанию этого поля;
    # 2. Если в list_columns модели списка нет поля
    # code, но есть поле name, то устанавливается
    # сортировка по возрастанию поля name;
    # Пример list_sort_order = ['code', '-name']
    list_sort_order = None

    # Окно для редактирования элемента справочника:
    add_window = None  # Нового
    edit_window = None  # Уже существующего

    # Флаг разрешающий/запрещающий удаление,
    # если None - то удаление возможно при наличии add_window/edit_window
    can_delete = None

    # классы отвечающие за отображение форм:
    list_window = ui.BaseListWindow  # Форма списка
    select_window = ui.BaseSelectWindow  # Форма выбора @UndefinedVariable

    #размеры окна выбора по умолчанию
    width, height = 510, 400

    MSG_DOESNOTEXISTS = _(
        u'Запись не найдена в базе данных.<br/>' +
        u'Возможно, она была удалена. Пожалуйста, обновите таблицу.')

    # плоский список полей фильтрации
    _all_search_fields = None

    # словарь data_index:sort_order
    _sort_fields = None

    # признак того, что Pack является основным для модели
    # (по основному паку строятся контролы DictSelectField
    # при автогонерации окон редактирования)
    _is_primary_for_model = True

    # функция, возвращающая экземпляр Pack, для укзанной по имени модели.
    # Реализация функции инжектируется при регистрации в Observable контроллер.
    @staticmethod
    def _get_model_pack(model_name):
        return None

    def __init__(self):
        super(ObjectPack, self).__init__()
        # В отличие от обычных паков в этом экшены создаются самостоятельно,
        # а не контроллером
        # Чтобы было удобно обращаться к ним по имени
        self.list_window_action = ObjectListWindowAction()
        self.select_window_action = ObjectSelectWindowAction()
        self.rows_action = ObjectRowsAction()
        # Но привязать их все равно нужно
        self.actions.extend([
            self.list_window_action,
            self.select_window_action,
            self.rows_action
        ])
        if self.add_window and not self.read_only:
            self.new_window_action = ObjectAddWindowAction()
            self.actions.append(self.new_window_action)
        else:
            self.new_window_action = None

        if self.edit_window and not self.read_only:
            self.edit_window_action = ObjectEditWindowAction()
            self.actions.append(self.edit_window_action)
        else:
            self.edit_window_action = None

        if (self.add_window or self.edit_window) and not self.read_only:
            self.save_action = ObjectSaveAction()
            self.actions.append(self.save_action)
        else:
            self.save_action = None

        if self.can_delete is None:
            self.can_delete = (
                self.add_window or self.edit_window) and not self.read_only
        if self.can_delete:
            self.delete_action = ObjectDeleteAction()
            self.actions.append(self.delete_action)
        else:
            self.delete_action = None

        # построение плоского списка колонок
        self._columns_flat = []
        self._all_search_fields = (self.search_fields or [])[:]
        self._sort_fields = {}

        def flatify(cols):
            for c in cols:
                sub_cols = c.get('columns', None)
                if sub_cols is not None:
                    flatify(sub_cols)
                else:
                    self._columns_flat.append(c)
                    data_index = c['data_index']
                    field = data_index.replace('.', '__')
                    # поле(поля) для сортировки
                    if c.get('sortable', False):
                        sort_fields = c.get('sort_fields', [field])
                        try:
                            sort_fields = list(sort_fields)
                        except:
                            sort_fields = [sort_fields]
                        self._sort_fields[data_index] = sort_fields
                    # поле для фильтрации
                    if c.get('searchable'):
                        search_fields = c.get('search_fields', [field])
                        try:
                            search_fields = list(search_fields)
                        except:
                            search_fields = [search_fields]
                        self._all_search_fields.extend(search_fields)
        flatify(self.columns)

    def replace_action(self, action_attr_name, new_action):
        """заменяет экшен в паке"""
        if getattr(self, action_attr_name, None):
            self.actions.remove(getattr(self, action_attr_name))
        setattr(self, action_attr_name, new_action)
        if getattr(self, action_attr_name):
            self.actions.append(getattr(self, action_attr_name))

    def get_default_action(self):
        """
        Возвращает действие по умолчанию
        (действие для значка на раб.столе/пункта меню)
        Используется пи упрощенном встраивании в UI (add_to_XXX=True)
        """
        return self.list_window_action

    def get_display_text(self, key, attr_name=None):
        """
        Возвращает отображаемое значение записи
        (или атрибута attr_name) по ключу key
        """
        row = self.get_row(key)
        if row is not None:
            try:
                text = getattr(row, attr_name)
            except AttributeError:
                try:
                    text = getattr(row, self.column_name_on_select)
                except AttributeError:
                    raise Exception(_(
                        u'Не получается получить поле {0} для '
                        u'DictSelectField.pack = {1}').format(attr_name, self))

            # getattr может возвращать метод, например verbose_name
            if callable(text):
                return text()
            else:
                return unicode(text)

    def get_edit_window_params(self, params, request, context):
        """
        Возвращает словарь параметров,
        которые будут переданы окну редактирования
        """
        return params

    def get_list_window_params(self, params, request, context):
        """
        Возвращает словарь параметров,
        которые будут переданы окну списка
        """
        return params

    def format_window_title(self, action):
        """
        Возвращает отформатированный заголовка окна.
        Заголовок примет вид "Модель: Действие"
        (например "Сотрудник: Добавление")
        """
        return "%s: %s" % (self.model._meta.verbose_name.capitalize(), action)

    #==================== ФУНКЦИИ ВОЗВРАЩАЮЩИЕ АДРЕСА =====================
    def get_list_url(self):
        """
        Возвращает адрес формы списка элементов справочника.
        Используется для присвоения адресов в прикладном приложении
        """
        return self.list_window_action.get_absolute_url()

    def get_select_url(self):
        """
        Возвращает адрес формы выбора из списка элементов справочника.
        Используется для присвоения адресов в прикладном приложении
        """
        return self.select_window_action.get_absolute_url()

    def get_edit_url(self):
        """
        Возвращает адрес формы редактирования элемента справочника
        """
        if self.edit_window_action:
            return self.edit_window_action.get_absolute_url()

    def get_rows_url(self):
        """
        Возвращает адрес, по которому запрашиваются элементы грида
        """
        return self.rows_action.get_absolute_url()

    def get_autocomplete_url(self):
        """
        Возвращает адрес для запроса элементов,
        подходящих введенному в поле тексту
        """
        return self.get_rows_url()

    def get_not_found_exception(self):
        """
        Возвращает класс исключения 'объект не найден'
        """
        return self.model.DoesNotExist

    def configure_grid(self, grid):
        """
        Конфигурирует grid для работы с этим паком,
        создает колонки и задает экшены
        """
        get_url = lambda x: x.get_absolute_url() if x else None
        grid.url_data = get_url(self.rows_action)
        if not self.read_only:
            grid.url_new = get_url(self.new_window_action)
            grid.url_edit = get_url(self.edit_window_action)
            grid.url_delete = get_url(self.delete_action)

        # построение колонок
        cc = ui.ColumnsConstructor()

        def populate(root, cols):
            for c in cols:
                sub_cols = c.get('columns', None)
                # параметры создаваемой колонки
                params = {}
                params.update(c)
                params.pop('columns', None)
                params.pop('searchable', None)
                params.pop('search_fields', None)
                params.pop('sort_fields', None)
                params.pop('filter', None)

                params['header'] = unicode(params.pop('header', ''))
                if not sub_cols is None:
                    new_root = cc.BandedCol(**params)
                    root.add(new_root)
                    populate(new_root, sub_cols)
                else:
                    root.add(cc.Col(**params))
        populate(cc, self.columns)
        cc.configure_grid(grid)

        #TODO перенести в класс грида, сделать метод add_search_field
        if self.get_search_fields():
            #поиск по гриду если есть по чему искать
            grid.top_bar.search_field = ExtSearchField(
                empty_text=_(u'Поиск'), width=200, component_for_search=grid)
            grid.top_bar.add_fill()
            grid.top_bar.items.append(grid.top_bar.search_field)

        grid.row_id_name = self.id_param_name
        grid.allow_paging = self.allow_paging
        grid.store.remote_sort = self.allow_paging

        filter_plugin = self.get_filter_plugin()
        if filter_plugin:
            grid.plugins.append(filter_plugin)

    def create_edit_window(self, create_new, request, context):
        """
        получить окно редактирования / создания объекта
        """
        if create_new:
            return self.add_window()
        else:
            return self.edit_window()

    def create_list_window(self, is_select_mode, request, context):
        """
        получить окно списка / выбора объектов
        is_select_mode - режим показа окна (True -выбор, False -список),
        """
        if is_select_mode:
            return self.select_window()
        else:
            return self.list_window()

    def handle_row_editing(self, request, context, data):
        """
        Метод принимает данные из редактируемого грида и возвращает
        результат редактирования кортежем вида
        (удачно/неудачно, "сообщение"/None)
        """
        return (False, None)

    def get_rows_query(self, request, context):
        """
        возвращает выборку из БД для получения списка данных
        """
        #q = super(,self).get_rows_query(request, context)
        #return q
        return self.model.objects.all().select_related()

    def get_search_fields(self, request=None, context=None):
        """Возвращает список data_index колонок по которым будет
        производиться поиск"""
        return self._all_search_fields[:]

    def get_sort_order(self, data_index, reverse=False):
        """Возвращает ключи сортировки для указанного data_index"""
        sort_order = self._sort_fields[data_index]
        if reverse:
            sort_order = ['-%s' % s for s in sort_order]
        return sort_order

    def apply_filter(self, query, request, context):
        """
        Применение фильтрации к выборке @query.
        Фильтрация может опираться на параметры запроса (@request/@context)
        """
        if hasattr(context, 'q'):
            request_filter = simplejson.loads(context.q)
            for item in request_filter:
                # Для дат
                if item['data']['value'] is basestring:
                    m = re.match(
                        r"([0-9]{2})\.([0-9]{2})\.([0-9]{4})$",
                        item['data']['value'])
                    if m:
                        item['data']['value'] = '{0}-{1}-{2}'.format(
                            *m.group(3, 2, 1)
                        )

                custom = None
                col = filter(
                    lambda col: col['data_index'] == item["field"],
                    self._columns_flat)[:1]
                if col:
                    custom = col[0]['filter'].get('custom_field')
                if custom:
                    #к нам пришел кастомный обработчик для фильтра
                    if callable(custom):
                        #если это метод, тады сразу фильтруем по его результату
                        q = custom(item['data']['value'])
                    else:
                        #в другом случае ожидается список полей
                        if item['data']['type'] == 'list':
                            params = [
                                models.Q(**dict(zip(
                                    ("%s__icontains" % custom_fld,),
                                    item['data']['value']
                                ))) for custom_fld in custom]
                        else:
                            params = [
                                models.Q(**{
                                    "%s__icontains" % custom_fld: (
                                        item['data']['value'])
                                }) for custom_fld in custom]

                        q = reduce(lambda q1, q2: q1 | q2, params)
                    query = query.filter(q)
                else:
                    query = query.filter(**{
                        "%s__icontains" % item['field']: item['data']['value']
                    })
        return query

    def apply_search(self, query, request, context):
        """Возвращает переданную выборку
        отфильторованной по параметрам запроса"""
        return m3_actions.utils.apply_search_filter(
            query,
            request.REQUEST.get('filter'),
            self.get_search_fields()
        )

    def apply_sort_order(self, query, request, context):
        """Возвращает переданную выборку
        отсортированной по параметрам запроса"""
        sorting_key = request.REQUEST.get('sort')
        if sorting_key:
            reverse = request.REQUEST.get('dir') == 'DESC'
            sort_order = self.get_sort_order(
                data_index=sorting_key,
                reverse=reverse)
            query = query.order_by(*sort_order)
        else:
            query = self.apply_default_sort_order(query)
        return query

    def apply_default_sort_order(self, query):
        """Возвращает выборку, отсортированную по-умолчанию"""
        if self.list_sort_order:
            query = query.order_by(*self.list_sort_order)
        return query

    def prepare_row(self, obj, request, context):
        """
        установка дополнительный атрибутов объекта
        перед возвратом json'a строк грида
        или может вернуть proxy_object
        obj из for obj in query из get_rows_query
        """
        return obj

    def get_row(self, row_id):
        """
        функция возвращает объект по иди
        используется в dictselectfield'ax
        Если id нет, значит нужно создать новый объект
        """
        if row_id == 0:
            record = self.model()
        else:
            record = self.model.objects.get(id=row_id)
        return record

    def get_obj(self, request, context):
        """
        Возвращает кортеж (объет, create_new)
        для создания, редатирования записи
        """
        obj_id = tools.extract_int(request, self.id_param_name) or 0
        create_new = (obj_id == 0)
        record = self.get_row(obj_id)
        return record, create_new

    def save_row(self, obj, create_new, request, context):
        """
        Сохраняет объект.
        При необходимости возбуждается ValidationError, или OverlapError
        """
        obj.save()

    def delete_row(self, obj_id, request, context):
        """
        Удаляет объект по @obj_id.
        Возвращает удалённый объект - т.е. объект модели,
        который уже не представлен в БД
        """
        obj = self.model.objects.get(id=obj_id)
        result = True
        if hasattr(obj, 'safe_delete'):
            result = obj.safe_delete()
        else:
            result = safe_delete(obj)
        #в случае успеха safe_delete возвращет true
        if not result:
            raise RelatedError(_(
                u'Не удалось удалить элемент {0}. '
                u'Возможно на него есть ссылки.'), format(obj_id))
        return obj

    def get_filter_plugin(self):
        """
        Возвращает плагин фильтрации
        """
        filter_items = []
        list_columns_filter = dict(
            (column['data_index'], column['filter'])
            for column in self._columns_flat
            if column.get('filter') and not column.get('columns'))
        if list_columns_filter:
            for k, v in list_columns_filter.items():
                params = {
                    'type': v.get('type', 'string'),
                    'data_index': k
                }
                f_options = v.get('options', [])
                if callable(f_options):
                    f_options = f_options()
                params['options'] = "[%s]" % ','.join(
                    (("'%s'" % item)
                        if isinstance(item, basestring) else
                        ((item is None and '[]') or ("['%s','%s']" % item)))
                    for item in f_options)
                filter_items.append("""{
                    type:'%(type)s',
                    dataIndex:'%(data_index)s',
                    options:%(options)s
                }""" % params)
            return """
                 new Ext.ux.grid.GridFilters({filters:[%s]})
            """ % ','.join(filter_items)

    #-----------------------------------------------------------------------
    # По умолчанию ни меню ни десктоп не расширяется
    # add_to_desktop = True
    # add_to_menu = True
    #
    # Если методы extend_menu/extend_desktop не реализованы,
    # меню будет расширяться на основе title и get_default_action
    #
    # Методы extend_X приоритетны
#    def extend_menu(self, menu):
#        """
#        Расширение главного меню.
#
#        Возвращаемый результат должен иметь вид:
#        return (
#            # добавление пунктов в меню "справочники"
#            menu.dicts(
#                menu.Item(u'Dict 1', self),
#                menu.SubMenu(u'Dict SubMenu',
#                    menu.Item(u'Dict 2', self.some_action),
#                ),
#            ),
#
#            # добавление пунктов в меню "реестры"
#            menu.registries(
#                menu.Item(u'Reg 1'),
#                menu.SubMenu(u'Regs SubMenu',
#                    menu.Item(u'Reg 2'),
#                ),
#            ),
#
#            # добавление пунктов в меню "администрирование"
#            menu.administry(
#                menu.Item(u'Admin item 1')
#            ),
#
#            # добавление пунктов в "корень" меню
#            menu.Item(name=u'item 1', self.some_action),
#
#            # добавление подменю в "корень" меню
#            menu.SubMenu(u'SubMenu',
#                menu.Item(u'Item 2', self.some_action),
#                menu.SubMenu(u'SubSubMenu',
#                    menu.Item(u'Item 3', self.some_action),
#                ),
#            ),
#        )
#
#        любой из элементов можно отключить вернув вместо него None.
#        например:
#            menu.Item(u'Name', url='/') if some_condition else None
#
#        Пустые подменю автоматически "схлопываются" (не видны в Главном Меню)
#        """
#        pass
#
#
#    def extend_desktop(self, desk):
#        """
#        Расширение Рабочего Стола.
#        Результат должен иметь вид:
#        return (
#            desk.Item(u'Ярлык 1', pack=self.list_action),
#            ...
#        )
#        любой из элементов можно отключить вернув вместо него None.
#        например:
#            desk.Item(u'Name', pack=self) if some_condition else None
#        """
#        pass


#==============================================================================
# SelectorWindowAction
#==============================================================================
class SelectorWindowAction(BaseAction):
    """
    Экшн показа окна выбора с пользовательским экшном обработки выбранных
    элементов. Например, множественный выбор элементов справочника, для
    последующего создания связок с ними.
    """
    url = r'/selector_window'

    # признак показа окна множественного выбора
    multi_select = True

    # url экшна обработки результата выбора
    callback_url = None

    # пак, объекты модели которого выбираются
    data_pack = None

    def configure_action(self, request, context):
        """
        Настройка экшна. Здесь нужно назначать пак и callback
        """
        pass

    def configure_context(self, request, context):
        """
        В данном методе происходит конфигурирование контекста для окна выбора.
        Возвращаемый результат должен быть экземпляром ActionContext.
        """
        return m3_actions.ActionContext()

    def configure_window(self, win, request, context):
        """
        В данном методе происходит конфигурирование окна выбора.
        """
        return win

    def run(self, request, context):
        """
        Выполнение экшна.
        Без крайней необходимости не перекрывать!
        """
        new_self = copy.copy(self)

        new_self.configure_action(request, context)

        assert new_self.data_pack, u'Не задан ActionPack-источник данных!'
        assert new_self.callback_url, u'Не задан Callback!'

        new_context = new_self.configure_context(request, context)

        # вызов экшна показа окна выбора
        win_result = new_self.data_pack.select_window_action.run(
            request, context)
        win = getattr(win_result, 'data', None)
        if not win:
            return win_result

        if not isinstance(win, ui.BaseSelectWindow):
            raise ApplicationLogicException(
                u'Класс окна выбора должен быть потомком BaseSelectWindow!')

        win = new_self.configure_window(win, request, context)

        win.callback_url = new_self.callback_url

        #if new_self.multi_select:
            #win.enable_multi_select()

        return m3_actions.ExtUIScriptResult(win, new_context)


def multiline_text_window_result(
        data, success=True, title=u'', width=600, height=500):
    """
    Формирование OpersionResult в виде многострочного окна,
    с размерами @width x @height и заголовком @title,
    отображающего текст @data :: string | iterable
    """
    if not isinstance(data, types.StringTypes):
        data = u'\n'.join(data)
    return m3_actions.OperationResult(
        success=success,
        code=(
            u"""
            (function() {
                var msg_win = new Ext.Window({
                    title: '%s',
                    width: %s, height: %s, layout:'fit',
                    items:[
                        new Ext.form.TextArea({
                            value: '%s',
                            readOnly: true,
                        })
                    ],
                    buttons:[{
                        text:'Закрыть',
                        handler: function(){ msg_win.close() }
                    }]

                })
                msg_win.show();
            })()
            """ % (
            title, width, height,
            data.replace("\n", r"\n").replace(r"'", r'"'))
        )
    )
