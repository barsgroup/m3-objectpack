#coding: utf-8
"""
Created on 23.07.12

@author: pirogov
"""
import inspect

from django.db import models as django_models

from m3.ui.ext import all_components as ext
from m3.ui.ext import windows as ext_windows
from m3.ui.ext.misc import store as ext_store
from m3.ui.ext.containers.grids import ExtGridColumn

import tools
from django.utils.translation import ugettext_lazy as _


#==============================================================================
# BaseWindow
#==============================================================================
class BaseWindow(ext_windows.ExtWindow):
    """
    Базовое окно
    """
    def __init__(self):
        super(BaseWindow, self).__init__()
        self._mro_exclude_list = []  # список исключений для make_read_only
        self._init_components()
        self._do_layout()

    def _init_components(self):
        """
        создание компонентов
        """
        pass

    def _do_layout(self):
        """
        растановка компонентов
        """
        pass

    def set_params(self, params):
        """
        установка параметров окна
        """
        if not getattr(self, 'title', None):
            self.title = params.get('title', u'')
        if params.get('read_only'):
            self.make_read_only()

    def make_read_only(self, access_off=True, exclude_list=None):
        """Управление состоянием Read-only окна"""
        super(BaseWindow, self).make_read_only(
            access_off, self._mro_exclude_list + (exclude_list or []))


#==============================================================================
# BaseEditWindow
#==============================================================================
class BaseEditWindow(ext_windows.ExtEditWindow, BaseWindow):
    """
    Базовое окно редактирования
    """
    @property
    def form(self):
        return self.__form

    def _init_components(self):
        super(BaseEditWindow, self)._init_components()
        self.__form = ext.ExtForm()
        self.items.append(self.form)
        # ОК:
        self.save_btn = ext.ExtButton(text=_(u'Сохранить'), handler="submitForm")
        # Отмена:
        self.cancel_btn = ext.ExtButton(text=_(u'Отмена'), handler="cancelForm")
        self._mro_exclude_list.append(self.cancel_btn)

    def _do_layout(self):
        super(BaseEditWindow, self)._do_layout()
        self.modal = True
        self.buttons.extend([
            self.save_btn,
            self.cancel_btn,
        ])
        # F2 -- ОК:
        f2key = {'key': 113, 'fn': self.save_btn.handler}
        self.keys.append(f2key)

    def set_params(self, params):
        """
        установка параметров окна
        """
        self.form.url = params['form_url']
        obj = params.get('object', None)
        if obj:
            self.form.from_object(obj)
        super(BaseEditWindow, self).set_params(params)


#==============================================================================
# BaseListWindow
#==============================================================================
class BaseListWindow(BaseWindow):
    """
    окно для отображения линейного справочника
    """
    def _init_components(self):
        """
        создание компонентов
        """
        self.grid = ext.ExtObjectGrid()
        self.grid_filters = {}
        self.close_btn = self.btn_close = ext.ExtButton(
            name='close_btn',
            text=_(u'Закрыть'),
            handler='function(){Ext.getCmp("%s").close();}' % self.client_id
        )
        self._mro_exclude_list.append(self.close_btn)

    def _do_layout(self):
        """
        растановка компонентов
        """
        self.maximizable = True
        self.minimizable = True
        self.layout = 'fit'
        self.items.append(self.grid)

        self.buttons.append(self.btn_close)

    def set_params(self, params):
        """
        установка параметров окна
        """
        assert 'pack' in params, 'incorrect params'
        params['pack'].configure_grid(self.grid)

        self.title = params.get('title')
        self.width = params.get('width')
        self.height = params.get('height')
        self.maximized = params.get('maximized', False)

    def add_grid_column_filter(self, column_name,
            filter_control=None, filter_name=None, tooltip=None):
        """ Добавление фильтра к колонке"""
        if not filter_name:
            filter_name = column_name
        if column_name in self.grid_filters:
            fltr = self.grid_filters[column_name]
        else:
            fltr = {}
        fltr[filter_name] = {
            'column_name': column_name,
            'filter_control': filter_control,
            'filter_name': filter_name,
            'tooltip': tooltip
        }
        self.grid_filters[column_name] = fltr

    def del_grid_column_filter(self, column_name, filter_name=None):
        """ Удаление фильтра с колонки"""
        if not filter_name:
            filter_name = column_name
        if column_name in self.grid_filters:
            if filter_name in self.grid_filters[column_name]:
                del self.grid_filters[column_name][filter_name]
            if len(self.grid_filters[column_name]) == 0:
                del self.grid_filters[column_name]

    def render_filter(self, filter_):
        lst = []
        if filter_['filter_control']:
            return filter_['filter_control']
        else:
            lst.append(u'xtype: "textfield"')
        if filter_['tooltip']:
            lst.append(u'tooltip: "%s"' % filter_['tooltip'])
        lst.append(u'filterName: "%s"' % filter_['filter_name'])
        return '{%s}' % ','.join(lst)

    def render(self):
        if self.grid:
            # добавим характеристики фильтров в колонки и подключим плагин
            if len(self.grid_filters) > 0:
                self.grid.plugins.append('new Ext.ux.grid.GridHeaderFilters()')
            for col in self.grid.columns:
                if col.data_index in self.grid_filters:
                    if len(self.grid_filters[col.data_index]) == 1:
                        filter_str = self.render_filter(
                            self.grid_filters[col.data_index].values()[0])
                    else:
                        filters = []
                        for fltr in self.grid_filters[col.data_index].values():
                            filters.append(self.render_filter(fltr))
                        filter_str = '[%s]' % ','.join(filters)
                    col.extra['filter'] = filter_str
        return super(BaseListWindow, self).render()


#==============================================================================
# BaseSelectWindow
#==============================================================================
class BaseSelectWindow(BaseListWindow):
    """
    окно выбора из линейного справочника
    """
    column_name_on_select = '__unicode__'

    def _init_components(self):
        super(BaseSelectWindow, self)._init_components()
        self.grid.handler_dblclick = 'selectValue'
        self.select_btn = ext.ExtButton(
            handler='selectValue', text=_(u'Выбрать'))
        self.buttons.insert(0, self.select_btn)
        self._mro_exclude_list.append(self.select_btn)
        self.grid.columns.append(ExtGridColumn(data_index='__unicode__',
            hidden=True))

    def set_params(self, params):
        """
        установка параметров окна
        """
        super(BaseSelectWindow, self).set_params(params)
        self.template_globals = 'select-window.js'


#==============================================================================
# ColumnsConstructor
#==============================================================================
class ColumnsConstructor(object):
    """
    Конструктор колонок для сложных гридов с banded-колонками

    Имеет 2 дочерних класса:
    - Col - простая колонка
    - BandedCol - группирующая колонка.

    Пример использования:

        # создание колонок inline

        cc = ColumnsConstructor()
        cc.add(
            cc.Col(header='1'),

            cc.BandedCol(header='2', items=(
                cc.Col(header='3'),
                cc.Col(header='4'),

                cc.BandedCol(header='5', items=(
                    cc.Col(header='6'),

                    cc.BandedCol(header='7', items=(
                        cc.Col(header='8'),
                        cc.Col(header='9'),
                        cc.BandedCol(),
                    )),

                    cc.Col(header='10')
                ))
            )),
            cc.Col(header='11')
        )

        # динамическое создание колонок
        for grp_idx in 'ABCD':
            grp = cc.BandedCol(header=grp_idx)

            for col_idx in 'ABCD':
                grp.add(
                    cc.Col(header=grp_idx + col_idx)
                )

            cc.add(grp)

        cc.configure_grid(grid)
    """

    class BandedCol(object):
        """
        Группирующая колонка
        """

        def __init__(self, items=None, **kwargs):
            """
            items - подчинённые колонки
            **kwargs - передаются в конструктор ExtGridColumn
            """
            params = {'header': ''}
            params.update(kwargs)
            self._column = ext.ExtGridColumn(**params)
            self.items = list(items or [])

        def add(self, *args):
            """
            Добавление колонок
            """
            self.items.extend(args)

        def _cleaned(self):
            """
            Возвращает элемент с очищенный от пустых подэлементов
            или None, если непустых подэлементов нет
            """
            self.items = filter(None, [i._cleaned() for i in self.items])
            return self if self.items else None

        def _normalized_depth(self):
            """
            Приведение всех подэлементов к одиному уровню вложенности
            Возвращается максимальная вложенность
            """
            depths = [i._normalized_depth() for i in self.items]
            max_depth = max(depths)

            new_items = []
            for depth, item in zip(depths, self.items):
                while depth < max_depth:
                    item = ColumnsConstructor.BandedCol(items=[item])
                    depth += 1
                new_items.append(item)
            self.items = new_items
            return max_depth + 1

        def _populate(self, grid, level, is_top_level=False):
            """
            Вставка колонок. Возвращается кол-во вставленных колонок
            """
            if is_top_level:
                if not self._cleaned():
                    return 0  # чистка
                level = self._normalized_depth()  # нормализация уровней
            else:
                grid.add_banded_column(self._column, level, 0)

            if not self.items:
                return 0

            cnt = sum([i._populate(grid, level - 1) for i in self.items])
            self._column.colspan = cnt

            return cnt

    class Col(object):
        """
        Простая колонка
        """
        def __init__(self, **kwargs):
            params = {'header': 'None'}
            params.update(kwargs)
            self._column = ext.ExtGridColumn(**params)

        def _cleaned(self):
            return self

        def _normalized_depth(self):
            return 1  # подэлементов нет, поэтому всегда вложенность 1

        def _populate(self, grid, level, is_top_level=False):
            grid.columns.append(self._column)
            return 1

    def __init__(self, items=None):
        self.items = list(items or [])

    def add(self, *args):
        """
        Добавление колонок
        """
        self.items.extend(args)

    def configure_grid(self, grid):
        """
        Конфигурирование грида
        """
        # все элементы суются в фейковую группирующую колонку,
        # которая отображаться не будет
        fake_col = self.BandedCol(items=self.items)
        fake_col._populate(grid, level=None, is_top_level=True)


#==============================================================================
# ModelEditWindow
#==============================================================================
class ModelEditWindow(BaseEditWindow):
    """
    Простое окно редактирования модели
    """
    # модель, для которой будет строится окно
    model = None

    # словарь kwargs для model_fields_to_controls ("field_list", и т.д.)
    field_fabric_params = None

    def _init_components(self):
        super(ModelEditWindow, self)._init_components()
        self._controls = model_fields_to_controls(
            self.model, self, **(self.field_fabric_params or {}))

    def _do_layout(self):
        super(ModelEditWindow, self)._do_layout()

        # автовысота окна
        self.height = None
        self.layout = 'form'
        self.layout_config = {'autoHeight': True}
        self.form.layout_config = {'autoHeight': True}

        # все поля добавляются на форму растянутыми по ширине
        self.form.items.extend(map(anchor100, self._controls))

    def set_params(self, params):
        super(ModelEditWindow, self).set_params(params)
        # если сгенерировано хотя бы одно поле загрузки файлов,
        # окно получает флаг разрешения загрузки файлов
        self.form.file_upload = any(
            isinstance(x, ext.ExtFileUploadField)
            for x in self._controls)

    @classmethod
    def fabricate(cls, model, **kwargs):
        """
        Гененрирует класс-потомок для конкретной модели.
        Использование:
        class Pack(...):
            add_window = ModelEditWindow.fabricate(
                SomeModel,
                field_list=['code', 'name'],
                model_register=observer,
            )
        """
        return type('%sEditWindow' % model.__name__, (cls,), {
            'model': model, 'field_fabric_params': kwargs})


#==============================================================================
def model_fields_to_controls(model, window,
        field_list=None, exclude_list=None,
        model_register=None, **kwargs):
    """
    Добавление на окно полей по полям модели,
    - входящим в список (строк) @field_list
    - не входящим в список (строк) @exclude_list
    exclude_list игнорируется при указанном field_list
    @kwargs - передача доп параметров в конструктор элементов

    Списки врлючения/исключения полей могут содержать
    wildcards вида 'x*' или '*x', которые трактуются как префиксы и суффиксы.

    При создании полей для связанных моделей ActionPack для модели ищется
    в реестре моделей @model_register по имени класса модели
    (передачей имени в метод "get" реестра)
    """
    def make_checker(patterns):
        matchers = []
        for pattern in patterns:
            if pattern.endswith('*'):
                fn = (lambda p: lambda s: s.startswith(p))(pattern[:-1])
            elif pattern.startswith('*'):
                fn = (lambda p: lambda s: s.endswith(p))(pattern[1:])
            else:
                fn = (lambda p: lambda s: s == p)(pattern)
            matchers.append(fn)
        if matchers:
            return (lambda s: any(fn(s) for fn in matchers))
        else:
            return lambda s: True

    if field_list:
        # генерация функции, разрешающей обработку поля
        is_valid = make_checker(list(field_list or ()))
    else:
        # генерация функции, запрещающей обработку поля
        is_valid = (lambda fn: lambda x: not fn(x))(
            make_checker(list(exclude_list or ()) + [
                'created', '*.created',
                'modified', '*.modified',
                'external_id', '*.external_id',
            ]))

    controls = []
    for f in model._meta.fields:
        if is_valid(f.attname):
            try:
                ctl = _create_control_for_field(f, model_register, **kwargs)
            except GenerationError:
                continue

            setattr(window, 'field__%s' % f.attname.replace('.', '__'), ctl)
            controls.append(ctl)

    return controls


class GenerationError(Exception):
    """
    ошибка возникает при проблемы генерации контрола
    """
    pass


def _create_control_for_field(f, model_register=None, **kwargs):
    """
    содает контроль для поля f = models.Field from model
    """
    name = f.attname

    if f.choices:
        ctl = make_combo_box(data=list(f.choices), **kwargs)

    elif isinstance(f, django_models.BooleanField):
        ctl = ext.ExtCheckBox(**kwargs)

    elif isinstance(f, (
            django_models.CharField,
            django_models.TimeField,  # время вводится в StringField
            )):
        ctl = ext.ExtStringField(max_length=f.max_length, **kwargs)

    elif isinstance(f, django_models.TextField):
        ctl = ext.ExtTextArea(**kwargs)

    elif isinstance(f, django_models.IntegerField):
        ctl = ext.ExtNumberField(**kwargs)

    elif isinstance(f, django_models.FloatField):
        ctl = ext.ExtNumberField(**kwargs)
        ctl.allow_decimals = True

    elif isinstance(f, (
            django_models.DateTimeField,
            django_models.DateField)):
        params = {'format': 'd.m.Y'}
        params.update(kwargs)
        ctl = ext.ExtDateField(**params)

    elif isinstance(f, django_models.ForeignKey):
        ctl = _create_dict_select_field(f, model_register, **kwargs)

    elif isinstance(f, django_models.ImageField):
        ctl = ext.ExtImageUploadField(**kwargs)

    elif isinstance(f, django_models.FileField):
        ctl = ext.ExtFileUploadField(**kwargs)

    else:
        raise GenerationError(u'Не могу сгенирировать контрол для %s' % f)

    ctl.name = name
    ctl.label = unicode(f.verbose_name)
    ctl.allow_blank = f.blank
    return ctl


def _create_dict_select_field(f, model_register=None, **kwargs):
    """
    Создает ExtDictSelectField по заданному ForeignKey-полю модели
    ActionPack предоставляется объектом @model_register через метод
    "get", в качестве параметра принимающий имя связанной модели.
    """
    related_model = f.rel.to.__name__

    pack = (model_register or {}).get(related_model)

    assert pack, 'Cant find pack for field %s (realated model %s)' % (
        f.name, related_model)

    params = {
        'display_field': pack.column_name_on_select,
        'value_field': 'id',
        'hide_edit_trigger': True,
        'hide_trigger': getattr(pack, 'allow_paging', False),
        'hide_clear_trigger': not f.blank,
        'hide_dict_select_trigger': False,
        'editable': False,
    }
    params.update(kwargs)

    ctl = ext.ExtDictSelectField(**params)
    ctl.url = pack.get_select_url()
    ctl.pack = pack.__class__
    ctl.name = f.attname
    if not ctl.name.endswith('_id'):
        ctl.name = '%s_id' % ctl.name

    return ctl


#==============================================================================
# WindowTab
#==============================================================================
class WindowTab(object):
    """
    Прототип конструктора таба для карточки сотрудника
    """
    # заголовок таба
    title = u''

    template = None  # js-шаблон для вкладки

    def _create_tab(self):
        return ext.ExtPanel(
            body_cls='x-window-mc',
            padding='5px',
            layout='form',
            title=self.title,
        )

    def init_components(self, win):
        """
        Здесь создаются компоненты, но не задаётся расположение
        Компоненты создаются, как атрибуты окна win
        """
        pass

    def do_layout(self, win, tab):
        """
        Здесь задаётся расположение компонентов. Компоненты должны
        быть расположены на табе tab окна win
        """
        pass

    def set_params(self, win, params):
        """
        Установка параметров
        """
        pass


#==============================================================================
# TabbedWindow
#==============================================================================
class TabbedWindow(BaseWindow):
    """
    Окно со вкладками
    """
    # описание классов вкладок (iterable)
    tabs = None

    template_globals = 'tabbed-window.js'

    def _init_components(self):
        # описание вкладок должно должны быть итерабельным
        assert tools.istraversable(self.tabs), 'Wrond type of "tabs"!'

        # инстанцирование вкладок
        instantiate = lambda x: x() if inspect.isclass(x) else x
        self.tabs = map(instantiate, self.tabs or [])

        # опредение вкладок не должно быть пустым
        # (проверка производится после инстанцирования,
        # т.к. описание колонок может быть итератором
        # и иметь истинное значение в булевом контексте)
        assert self.tabs, '"tabs" can not be empty!'

        super(TabbedWindow, self)._init_components()

        # контейнер для вкладок
        self._tab_container = ext.ExtTabPanel(deferred_render=False)

        # создание компонентов для вкладок
        for con in self.tabs:
            con.init_components(win=self)

    def _do_layout(self):
        super(TabbedWindow, self)._do_layout()

        # настройка отображения окна
        self.layout = 'fit'
        self.width, self.height = 600, 450
        self.min_width, self.min_height = self.width, self.height

        self.maximizable = self.minimizable = True

        # размещение контролов во вкладках
        for con in self.tabs:
            tab = con._create_tab()
            con.do_layout(win=self, tab=tab)
            self._tab_container.items.append(tab)

        # размещение контейнера вкладок на форму
        tc = self._tab_container
        tc.anchor = '100%'
        tc.layout = 'fit'
        tc.auto_scroll = True
        self.items.append(tc)

    def set_params(self, params):
        # установка параметров вкладок, формирование списка шаблонов вкладок
        self.tabs_templates = []
        for con in self.tabs:
            if con.template:
                self.tabs_templates.append(con.template)
            con.set_params(win=self, params=params)

        # отключение поиска в гридах во вкладках
        # т.к. рендеринг оного работает неправильно
        # TODO: найти причину
        for grid in tools.find_element_by_type(
                self._tab_container, ext.ExtObjectGrid):
            if hasattr(grid.top_bar, 'search_grid'):
                grid.top_bar.search_grid.hidden = True

        super(TabbedWindow, self).set_params(params)


#==============================================================================
# TabbedEditWindow
#==============================================================================
class TabbedEditWindow(TabbedWindow, BaseEditWindow):
    """
    Окно редактирования с вкладками
    """
    def _do_layout(self):
        super(TabbedEditWindow, self)._do_layout()
        self.items.remove(self._tab_container)
        self.form.items.append(self._tab_container)
        self.form.layout = 'fit'


#==============================================================================
# ComboBoxWithStore
#==============================================================================
class ObjectGridTab(WindowTab):
    """
    Вкладка с гридом
    """
    _pack_instance = None

    @property
    def title(self):
        return self._pack.title

    @property
    def _pack(self):
        # кэшированная ссылка на пак
        self._pack_instance = self._pack_instance or self.get_pack()
        return self._pack_instance

    def get_pack(self):
        """
        Возвращает экземпляр ObjectPack для настройки грида
        """
        raise NotImplementedError()

    def _create_tab(self):
        tab = super(ObjectGridTab, self)._create_tab()
        tab.layout = 'fit'
        return tab

    def init_components(self, win):
        # создание грида
        self.grid = ext.ExtObjectGrid()
        setattr(win, '%s_grid' % self.__class__.__name__, self.grid)

    def do_layout(self, win, tab):
        # помещение грида во вкладку
        tab.items.append(self.grid)

    def set_params(self, win, params):
        # настройка
        self._pack.configure_grid(self.grid)

    @classmethod
    def fabricate_from_pack(
            cls, pack_name, pack_register, tab_class_name=None):
        """
        Возвращает класс вкладки, построенной на основе
        пака с именем @pack_name. В процессе настройки вкладки
        экземпляр пака получается посредством
        вызова @pack_getter.get_pack_instance для @pack_name.

        @tab_class_name - имя класса вкладки (если не указано,
            то генерируется на основе имени класса модели пака)
        """
        tab_class_name = tab_class_name or (
            '%sTab' % pack_name.replace('/', '_'))
        return type(
            tab_class_name, (cls,),
            {'get_pack': lambda self: (
                pack_register.get_pack_instance(pack_name)
            )}
        )

    @classmethod
    def fabricate(cls, model, model_register, tab_class_name=None):
        """
        Возвращает класс вкладки, построенной на основе основного
        пака для модели @model. В процессе настройки вкладки
        экземпляр пака получается посредством
        вызова @model_register.get для @model_name.

        @tab_class_name - имя класса вкладки (если не указано,
            то генерируется на основе имени класса модели пака)
        """
        tab_class_name = tab_class_name or ('%sTab' % model.__name__)
        return type(
            tab_class_name, (cls,),
            {'get_pack': lambda self: model_register.get(model.__name__)}
        )


class ObjectTab(WindowTab):
    """
    Вкладка редактирования полей объекта
    """
    # модель, для которой будет строится окно
    model = None

    # словарь kwargs для model_fields_to_controls ("field_list", и т.д.)
    field_fabric_params = None

    @property
    def title(self):
        return unicode(
            self.model._meta.verbose_name or
            repr(self.model)
        )

    def init_components(self, win):
        super(ObjectTab, self).init_components(win)
        self._controls = model_fields_to_controls(
            self.model, self, **(self.field_fabric_params or {}))

    def do_layout(self, win, tab):
        super(ObjectTab, self).do_layout(win, tab)

        # автовысота вкладки
        tab.height = None
        tab.layout = 'form'
        tab.layout_config = {'autoHeight': True}

        # все поля добавляются на форму растянутыми по ширине
        tab.items.extend(map(anchor100, self._controls))

    def set_params(self, win, params):
        super(ObjectTab, self).set_params(win, params)
        # если сгенерировано хотя бы одно поле загрузки файлов,
        # окно получает флаг разрешения загрузки файлов
        win.form.file_upload = win.form.file_upload or any(
            isinstance(x, ext.ExtFileUploadField)
            for x in self._controls)

    @classmethod
    def fabricate(cls, model, **kwargs):
        """
        Гененрирует класс-потомок для конкретной модели.
        Использование:
        class Pack(...):
            add_window = ObjectTab.fabricate(
                SomeModel,
                field_list=['code', 'name'],
                model_register=observer,
            )
        """
        return type('%sTab' % model.__name__, (cls,), {
            'model': model, 'field_fabric_params': kwargs})


#==============================================================================
# ComboBoxWithStore
#==============================================================================
class ComboBoxWithStore(ext.ExtComboBox):
    """
    Потомок m3-комбобокса со втроенным стором
    Контрол имеет два свойства:
        data - фиксированный стор вида ((id, name),....)
        url - url для динамической загрузки
    Установка любого из этих свойств конфигурирует стор контрола
    """

    def __init__(self, data=None, url=None, **kwargs):
        super(ComboBoxWithStore, self).__init__(**kwargs)
        self._make_store(data, url)

    def _make_store(self, data=None, url=None):
        if url:
            self.store = ext_store.ExtJsonStore(url=url)
            self.store.root = 'rows'
        else:
            self.store = ext_store.ExtDataStore(data or ((0, ''),))

    @property
    def data(self):
        return self.store.data

    @data.setter
    def data(self, data):
        self._make_store(data=data)

    @property
    def url(self):
        return self.store.url

    @url.setter
    def url(self, url):
        self._make_store(url=url)


def make_combo_box(**kwargs):
    """
    Создает и возвращает ExtComboBox
    """
    params = dict(
        display_field='name',
        value_field='id',
        trigger_action_all=True,
        editable=False,
    )
    params.update(kwargs)
    return ComboBoxWithStore(**params)


#==============================================================================
def anchor100(ctl):
    """
    Устанавливает anchor в 100% у контрола и восвращает его (контрол)
    Пример использования:
        controls = map(anchor100, controls)
    """
    if not isinstance(ctl, django_models.DateField):
        tools.modify(ctl, anchor='100%')
    return ctl


allow_blank = lambda ctl: tools.modify(ctl, allow_blank=True)
allow_blank.__doc__ = """
    Устанавливает allow_blank=True у контрола и восвращает его (контрол)
    Пример использования:
        controls = map(allow_blank, controls)
    """

deny_blank = lambda ctl: tools.modify(ctl, allow_blank=False)
deny_blank.__doc__ = """
    Устанавливает allow_blank=False у контрола и восвращает его (контрол)
    Пример использования:
        controls = map(allow_blank, controls)
    """
