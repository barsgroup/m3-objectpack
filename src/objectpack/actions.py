#coding: utf-8
'''
Created on 23.07.2012

@author: pirogov
'''

import copy
import datetime

from django.db.models import fields as dj_fields
from django.utils.encoding import force_unicode

from m3.ui import actions as m3_actions

from m3.ui.actions.interfaces import ISelectablePack
from m3.core.exceptions import RelatedError, ApplicationLogicException
from m3.db import safe_delete
from m3.ui.ext.fields.complex import ExtSearchField

import ui, tools


class BaseWindowAction(m3_actions.Action):
    '''
    базовый Группа который возвращает окно
    '''
    win_params = {} #параметы для формирования окна
    request = None #request выолнения
    context = None #context выполнения, будет возвращен экшеном
    win = None #экземпляр окна которое вернет экшен

    def create_window(self):
        '''
        создает объект окна
        например self.win = EditWindow()
        '''
        raise NotImplementedError()

    def set_windows_params(self):
        '''
        заполняет словарь win_params
        например self.win_params['title'] = u'Привет из ада'
        '''
        pass

    def _apply_windows_params(self):
        '''
        передает параметры в экземлпяр окна
        перекрывается в крайних случаях
        '''
        self.win.set_params(self.win_params)

    def configure_window(self):
        '''
        дополнительно конфигурирует окно,
        только через функции окна,
        например self.win.make_read_only()
        никакого self.win.grid.top_bar.items[8].text = u'Ух ты, 9 кнопок'
        '''
        pass

    def run(self, request, context):
        '''
        сам обработчки, перекрывает в крайних случаях
        '''
        new_self = copy.copy(self)
        new_self.win_params = (self.__class__.win_params or {}).copy()
        new_self.request = request
        new_self.context = context
        new_self.set_windows_params()
        new_self.create_window()
        new_self._apply_windows_params()
        new_self.configure_window()
        return m3_actions.ExtUIScriptResult(
            new_self.win, context=new_self.context)


class ObjectListWindowAction(BaseWindowAction):
    '''
    Действие, которое возвращает окно со списком элементов справочника.
    '''
    url = '/list-window$'
    is_select_mode = False #режим показа окна (True - выбор, False - список),

    def set_windows_params(self):
        params = self.win_params
        params['pack'] = self.parent
        params['title'] = self.parent.title
        params['is_select_mode'] = self.is_select_mode
        params['id_param_name'] = self.parent.id_param_name
        params['height'] = self.parent.height
        params['width'] = self.parent.width
        params['read_only'] = not self.parent.has_sub_permission(
            self.request.user, self.parent.PERM_EDIT, self.request)
        self.win_params = self.parent.get_list_window_params(
            params, self.request, self.context)

    def create_window(self):
        self.win = self.parent.create_list_window(
            is_select_mode=self.win_params['is_select_mode'],
            request=self.request,
            context=self.context)


class ObjectSelectWindowAction(ObjectListWindowAction):
    '''
    Действие, возвращающее окно выбора из справочника
    '''
    url = '/select-window$'
    is_select_mode = True


class ObjectEditWindowAction(BaseWindowAction):
    '''
    редактирование элемента справочника
    '''
    url = '/edit-window$'

    def set_windows_params(self):
        try:
            obj, create_new = self.parent.get_obj(self.request, self.context)
        except self.parent.get_not_found_exception():
            raise ApplicationLogicException(self.parent.MSG_DOESNOTEXISTS)

        self.win_params['object'] = obj
        self.win_params['create_new'] = create_new
        self.win_params['form_url'] = self.parent.save_action.get_absolute_url()

        # заголовок окна по-умолчанию
        self.win_params['title'] = self.parent.format_window_title(
            u'Добавление' if create_new else u'Редактирование')

        self.win_params = self.parent.get_edit_window_params(
            self.win_params, self.request, self.context)


    def create_window(self):
        'вернем окно для создания или редактирования'
        assert self.win_params.has_key('create_new'), (
            u'может забыли вызвать родителький set_windows_params?')
        self.win = self.parent.create_edit_window(
            self.win_params['create_new'], self.request, self.context)

    def configure_window(self):
        'настройка окна'
        # проверим право редактирования
        if not self.parent.has_sub_permission(
                self.request.user, self.parent.PERM_EDIT, self.request):
            exclude_list = ['close_btn', 'cancel_btn']
            self.win.make_read_only(True, exclude_list)


class ObjectSaveAction(m3_actions.Action):
    '''
    Действие выполняет сохранение новой записи в справочник
    в любом месте можно райзить ApplicationLogicException
    '''
    url = '/save$'
    request = None
    context = None
    win = None
    obj = None
    create_new = None

    def create_window(self):
        'вернем окно для создания или редактирования'
        self.win = self.parent.create_edit_window(self.create_new, self.request, self.context)

    def create_obj(self):
        'создание объекта'
        try:
            self.obj, self.create_new = self.parent.get_obj(self.request, self.context)
        except self.parent.get_not_found_exception():
            raise ApplicationLogicException(self.parent.MSG_DOESNOTEXISTS)

    def bind_win(self):
        'биндим форму к реквесту'
        self.win.form.bind_to_request(self.request)

    def bind_to_obj(self):
        'биднинг формы к объекту'
        self.win.form.to_object(self.obj)

    def save_obj(self):
        'сохранеие объекта'
        self.parent.save_row(self.obj, self.create_new, self.request, self.context)

    def run(self, request, context):
        new_self = copy.copy(self)
        new_self.request = request
        new_self.context = context
        new_self.create_obj()
        new_self.create_window()
        new_self.bind_win()
        new_self.bind_to_obj()
        new_self.save_obj()
        return m3_actions.OperationResult()


class ObjectRowsAction(m3_actions.Action):
    '''
    Возвращает данные для грида справочника
    '''
    url = '/rows$'
    request = None
    context = None
    query = None

    def set_query(self):
        '''устанавливает запрос к базе'''
        self.query = self.parent.get_rows_query(self.request, self.context)

    def apply_filter(self):
        '''устанавливает поисковый фильтр'''
        self.query = m3_actions.utils.apply_search_filter(
            self.query,
            self.request.REQUEST.get('filter'),
            self.get_filter_fields()
        )

    def get_filter_fields(self):
        '''
        возвращает список колонок для фильтрации,
        например, ['school__name']
        '''
        if hasattr(self.parent, 'get_filter_fields'):
            return self.parent.get_filter_fields(self.request, self.context)

    def apply_sort_order(self):
        'устанавливает сортировку'

        direction = self.request.REQUEST.get('dir')
        sort_order = self.request.REQUEST.get('sort')
        if sort_order:
            sort_order = sort_order.replace('.', '__')
            if direction == 'DESC':
                sort_order = ['-' + sort_order, ]
            else:
                sort_order = [sort_order, ]
        else:
            sort_order = self.get_sort_fields()
        if sort_order:
            self.query = self.query.order_by(*sort_order)

    def get_sort_fields(self):
        '''
        возвращает список колонок для фильтрации
        '''
        return getattr(self.parent, 'list_sort_order', [])

    def apply_limit(self):
        'обрезает по текущей странице'
        if getattr(self.parent, 'allow_paging', True):
            offset = m3_actions.utils.extract_int(self.request, 'start')
            limit = m3_actions.utils.extract_int(self.request, 'limit')
        else:
            offset = limit = 0
        self.query = tools.QuerySplitter(self.query, offset, limit)

    def get_rows(self):
        'преобразует query в лист'
        res = []
        for obj in self.query:
            prep_obj = self.prepare_object(obj)
            if prep_obj:
                res.append(prep_obj)
            else:
                self.query.skip_last()
        return res

    def prepare_object(self, obj):
        '''
        возвращает словарь для составления результирующего списка
        на вход получает объект, полученный из QuerySet'a
        '''
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

                if isinstance(obj, datetime.date):
                    obj = obj.strftime('%d.%m.%Y')

                result[col] = force_unicode(obj)

        #заполним объект данными по дата индексам
        for col in self.get_column_data_indexes():
            parse_data_indexes(obj, col, result_dict)

        return result_dict


    def get_total_count(self):
        'подсчет общего кол-ва объектов'
        return self.query.count()

    def get_column_data_indexes(self):
        'список дата индеков для формирования jsona'
        res = []
        for col in getattr(self.parent, 'columns', []):
            res.append(col['data_index'])
        res.append(self.parent.id_field)
        return res

    def run(self, request, context):
        new_self = copy.copy(self)
        new_self.request = request
        new_self.context = context
        new_self.set_query()
        new_self.apply_filter()
        new_self.apply_sort_order()
        total_count = new_self.get_total_count()
        new_self.apply_limit()
        rows = new_self.get_rows()
        return m3_actions.PreJsonResult({
            'rows':  rows,
            'total': total_count
        })


class ObjectDeleteAction(m3_actions.Action):
    '''
    экшен удаления
    '''

    url = '/delete_row$'
    request = None
    context = None

    def try_delete_objs(self):
        '''
        удаляет обекты и пытается перехватить исключения
        '''
        try:
            self.delete_objs()
        except RelatedError, e:
            raise ApplicationLogicException(e.args[0])
        except Exception, e:
            if e.__class__.__name__ == 'IntegrityError':
                message = u'Не удалось удалить элемент. Возможно на него есть ссылки.'
                raise ApplicationLogicException(message)
            else:
                # все левые ошибки выпускаем наверх
                raise

    def delete_objs(self):
        '''
        удаляет обекты
        '''
        ids = m3_actions.utils.extract_int_list(
            self.request, self.parent.id_param_name)
        for i in ids:
            self.delete_obj(i)


    def delete_obj(self, id_):
        'удаление конкретного объекта'
        obj = self.parent.delete_row(id_, self.request, self.context)
        self.audit(obj)

    def run(self, request, context):
        new_self = copy.copy(self)
        new_self.request = request
        new_self.context = context
        new_self.try_delete_objs()
        return m3_actions.OperationResult()


class ObjectPack(m3_actions.ActionPack, ISelectablePack):
    '''
    Пакет с действиями, специфичными для работы с редактирование модели
    '''
    # Заголовок окна справочника
    # если не перекрыт в потомках - берется из модели
    @property
    def title(self):
        return unicode(
            self.model._meta.verbose_name_plural or
            self.model._meta.verbose_name or
            repr(self.model))

    # Список колонок состоящий из словарей
    # все параметры словаря передаются в add_column
    # список параметров смотри в BaseExtGridColumn
    # кроме filterable - признак что колонка будет учавтовать в фильтрации

    url = u'/pack'

    columns = [
#        {
#            'data_index':'fullname',
#            'width':,
#            'header':u'',
#            'filterable':True,
#            'sortable':True,
#        },
#        {
#            'data_index':'school.name',
#            'width':200,
#            'header':u'Колонка 1',
#            'filterable':True
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

    #название поля идентифицирующий объект
    #это названия параметра, который бедт передоваться в post запрос редактирования, удаления
    id_param_name = 'id'
    #data_index колонки, идентифицирующей объект
    #этот параметр будет браться из модели и передаваться как ID в ExtDataStore
    #т.е в post запросе редактирования будет лужеть {id_param_name:obj.id_field}
    id_field = 'id'

    # поле/метод, предоставляющее значение для отображения в DictSelectField
    # ПОКА НЕ РАБОТАЕТ извлечение вложенных полей - конфликт с ExtJS
    column_name_on_select = 'name'

    # Список дополнительных полей модели по которым будет идти поиск
    # основной список береться из colums по признаку filterable
    filter_fields = []
    allow_paging = True

    #пак будет настраивать грид на возможность редактирования
    read_only = False

    # Порядок сортировки элементов списка. Работает следующим образом:
    # 1. Если в list_columns модели списка есть поле code, то устанавливается сортировка по возрастанию этого поля;
    # 2. Если в list_columns модели списка нет поля code, но есть поле name, то устанавливается сортировка по возрастанию поля name;
    # Пример list_sort_order = ['code', '-name']
    list_sort_order = None

    # Окно для редактирования элемента справочника:
    add_window = None  # Нового
    edit_window = None # Уже существующего

    # Флаг разрешающий/запрещающий удаление,
    # если None - то удаление возможно при наличии add_window/edit_window
    can_delete = None

    # Группа отвечающие за отображение форм:
    list_window = ui.BaseListWindow # Форма списка
    select_window = ui.BaseSelectWindow # Форма выбора @UndefinedVariable

    #размеры окна выбора по умолчанию
    width, height = 510, 400

    # права доступа для базовых справочников
    PERM_EDIT = 'edit'
    sub_permissions = {PERM_EDIT: u'Редактирование'}

    MSG_DOESNOTEXISTS = (u'Запись не найдена в базе данных.<br/>' +
        u'Возможно, она была удалена. Пожалуйста, обновите таблицу.')

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
            self.new_window_action = ObjectEditWindowAction()
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


    def replace_action(self, action_attr_name, new_action):
        '''заменяет экшен в паке'''
        if getattr(self, action_attr_name, None):
            self.actions.remove(getattr(self, action_attr_name))
        setattr(self, action_attr_name, new_action)
        if getattr(self, action_attr_name):
            self.actions.append(getattr(self, action_attr_name))

    def get_autocomplete_url(self):
        """ Получить адрес для запроса элементов
        подходящих введенному в поле тексту """
        return self.get_rows_url()

    def get_display_text(self, key, attr_name=None):
        """ Получить отображаемое значение записи
        (или атрибута attr_name) по ключу key """
        row = self.get_row(key)
        if row is not None:
            try:
                text = getattr(row, attr_name)
            except AttributeError:
                try:
                    text = getattr(row, self.column_name_on_select)
                except AttributeError:
                    raise Exception(
                        u'Не получается получить поле %s для '
                        u'DictSelectField.pack = %s' % (attr_name, self))

            # getattr может возвращать метод, например verbose_name
            if callable(text):
                return text()
            else:
                return unicode(text)

    def get_edit_window_params(self, params, request, context):
        '''
        возвращает словарь параметров которые будут переданы окну редактирования
        '''
        return params

    def get_list_window_params(self, params, request, context):
        '''
        возвращает словарь параметров которые будут переданы окну списка
        '''
        return params

    def format_window_title(self, action):
        '''
        Форматирование заголовка окна.
        Заголовок примет вид "Модель: Действие"
        (например "Сотрудник: Добавление")
        '''
        return "%s: %s" % (self.model._meta.verbose_name, action)


    #==================== ФУНКЦИИ ВОЗВРАЩАЮЩИЕ АДРЕСА =====================
    def get_list_url(self):
        '''
        Возвращает адрес формы списка элементов справочника.
        Используется для присвоения адресов в прикладном приложении.
        '''
        return self.list_window_action.get_absolute_url()

    def get_select_url(self):
        '''
        Возвращает адрес формы списка элементов справочника.
        Используется для присвоения адресов в прикладном приложении.
        '''
        return self.select_window_action.get_absolute_url()

    def get_edit_url(self):
        '''
        Возвращает адрес формы редактирования элемента справочника.
        '''
        return self.edit_window_action.get_absolute_url()

    def get_rows_url(self):
        '''
        Возвращает адрес по которому запрашиваются элементы грида
        '''
        return self.rows_action.get_absolute_url()

    def get_not_found_exception(self):
        '''возвращает Группа исключения "не найден"'''
        return self.model.DoesNotExist

    def get_default_action(self):
        """docstring for get_default_action"""
        return self.list_window_action

    def configure_grid(self, grid):
        '''
        конфигурирования grid для работы с этим паком
        создает колонки и задает экшены
        '''
        get_url = lambda x: x.get_absolute_url() if x else None
        grid.url_data = get_url(self.rows_action)
        if not self.read_only:
            grid.url_new = get_url(self.new_window_action)
            grid.url_edit = get_url(self.edit_window_action)
            grid.url_delete = get_url(self.delete_action)

        for col in self.columns:
            temp = {}
            temp.update(col)
            if temp.has_key('filterable'):
                temp.pop('filterable')
            grid.add_column(**temp)

        #TODO перенести в Группа грида сделать метод add_search_field
        if self.get_filter_fields():
            #поиск по гриду если есть по чему искать
            grid.top_bar.search_field = ExtSearchField(
                empty_text=u'Поиск', width=200, component_for_search=grid)
            grid.top_bar.add_fill()
            grid.top_bar.items.append(grid.top_bar.search_field)

        grid.row_id_name = self.id_param_name
        grid.allow_paging = self.allow_paging
        grid.store.remote_sort = self.allow_paging

    def get_filter_fields(self, request=None, context=None):
        'возвращает список data_index колонок по которым будет вестить поиск'
        #софрмируем полный список колонок для фильтрации
        _all_filter_fields = []
        for col in self.columns:
            if col.get('filterable'):
                _all_filter_fields.append(col['data_index'])
        _all_filter_fields.extend(self.filter_fields)
        _all_filter_fields = map(lambda x:x.replace('.', '__'), _all_filter_fields)
        return _all_filter_fields

    def create_edit_window(self, create_new, request, context):
        '''
        получить окно редактирования/создания объекта
        '''
        if create_new:
            return self.add_window()
        else:
            return self.edit_window()

    def create_list_window(self, is_select_mode, request, context):
        '''
        получить окно списка/выбора объектов
        is_select_mode - режим показа окна (True - выбор, False - список),
        '''
        if is_select_mode:
            return self.select_window()
        else:
            return self.list_window()

    def get_rows_query(self, request, context):
        '''
        возвращает кварисет для получения списка данных
        '''
        #q = super(,self).get_rows_query(request, context)
        #return q
        return self.model.objects.all().select_related()

    def prepare_row(self, obj, request, context):
        '''
        установка дополнительный атрибутов объекта
        перед возвратом json'a строк грида
        или может вернуть proxy_object
        obj из for obj in query из get_rows_query
        '''
        return obj

    def get_row(self, row_id):
        '''
        функция возвращает объект по иди
        используется в dictselectfield'ax
        Если id нет, значит нужно создать новый объект
        '''
        if row_id == 0:
            record = self.model()
        else:
            record = self.model.objects.get(id=row_id)
        return record

    def get_obj(self, request, context):
        '''
        возвращает tuple (объет, create_new)
        для создания, редатирования записи
        '''
        obj_id = m3_actions.utils.extract_int(request, self.id_param_name)
        create_new = (obj_id == 0)
        record = self.get_row(obj_id)
        return record, create_new

    def save_row(self, obj, create_new, request, context):
        '''
        сохраняет объект
        при необходимости делается raise ApplicationLogicException
        '''
        obj.save()

    def delete_row(self, obj_id, request, context):
        '''
        удаление объекта
        если вернет модель то она отдасться аудитору
        '''

        obj = self.model.objects.get(id=obj_id)
        result = True
        if hasattr(obj, 'safe_delete'):
            result = obj.safe_delete()
        else:
            result = safe_delete(obj)
        #в случе успеха safe_delete возвращет true
        if not result:
            raise RelatedError(u'Не удалось удалить элемент %s. '
                u'Возможно на него есть ссылки.' % obj_id)
        return obj


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
#        '''
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
#        '''
#        pass
#
#
#    def extend_desktop(self, desk):
#        '''
#        Расширение Рабочего Стола.
#        Результат должен иметь вид:
#        return (
#            desk.Item(u'Ярлык 1', pack=self.list_action),
#            ...
#        )
#        любой из элементов можно отключить вернув вместо него None.
#        например:
#            desk.Item(u'Name', pack=self) if some_condition else None
#        '''
#        pass


#===============================================================================
# SelectorWindowAction
#===============================================================================
class SelectorWindowAction(m3_actions.Action):
    '''
    Экшн показа окна выбора с пользовательским экшном обработки выбранных
    элементов. Например, множественный выбор элементов справочника, для
    последующего создания связок с ними.
    '''
    url = r'/selector_window'

    # признак показа окна множественного выбора
    multi_select = True

    # url экшна обработки результата выбора
    callback_url = None

    # пак, объекты модели которого выбираются
    data_pack = None


    def configure_action(self, request, context):
        '''
        Настройка экшна. Здесь нужно назначать пак и callback
        '''
        pass


    def configure_context(self, request, context):
        '''
        В данном методе происходит конфигурирование контекста для окна выбора.
        Возвращаемый результат должен быть экземпляром ActionContext.
        '''
        return m3_actions.ActionContext()


    def configure_window(self, win, request, context):
        '''
        В данном методе происходит конфигурирование окна выбора.
        '''
        return win


    def run(self, request, context):
        '''
        Выполнение экшна.
        Без крайней необходимости не перекрывать!
        '''
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

        if new_self.multi_select:
            win.enable_multi_select()

        return m3_actions.ExtUIScriptResult(win, new_context)

