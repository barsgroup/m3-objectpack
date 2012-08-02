#coding: utf-8
'''
Created on 23.07.12

@author: pirogov
'''
from django.db import models as django_models

from m3.ui.ext import all_components as ext
from m3.ui.ext import windows as ext_windows
from m3.ui.ext .misc import store as ext_store
from m3.helpers import urls as m3_urls

import tools


class _BaseWindowExtender(object):
    '''
    Группа для описания методов
    конструирования и настройки окна
    '''

    def _initialize(self):
        self._init_components()
        self._do_layout()

    def _init_components(self):
        '''
        создание компонентов
        '''
        pass

    def _do_layout(self):
        '''
        растановка компонентов
        '''
        pass

    def set_params(self, params):
        '''
        установка параметров окна
        '''
        if not getattr(self, 'title', None):
            self.title = params.get('title', u'')
        if params.get('read_only'):
            self.make_read_only()


#===============================================================================
# BaseWindow
#===============================================================================
class BaseWindow(ext_windows.ExtWindow, _BaseWindowExtender):
    '''базовое окно'''

    def make_read_only(self, access_off=True, exclude_list=None):
        '''Управление состоянием Read-only окна'''
        super(BaseWindow, self).make_read_only(
            access_off, self._mro_exclude_list + (exclude_list or []))

    def __init__(self):
        super(BaseWindow, self).__init__()
        self._mro_exclude_list = [] # список исключений для make_read_only
        self._initialize()


#===============================================================================
# BaseEditWindow
#===============================================================================
class BaseEditWindow(ext_windows.ExtEditWindow, _BaseWindowExtender):
    '''базовое окно редактирования'''

    def __init__(self):
        super(BaseEditWindow, self).__init__()
        self._mro_exclude_list = [] # список исключений для make_read_only
        self._initialize()

    def _init_components(self):
        self.form = ext.ExtForm()
        # ОК:
        self.save_btn = ext.ExtButton(text=u'Сохранить', handler="submitForm")
        # Отмена:
        self.cancel_btn = ext.ExtButton(text=u'Отмена', handler="cancelForm")
        self._mro_exclude_list.append(self.cancel_btn)

    def _do_layout(self):
        self.modal = True
        self.buttons.extend([
            self.save_btn,
            self.cancel_btn,
            ])
        # F2 -- ОК:
        f2key = {'key' : 113, 'fn' : self.save_btn.handler}
        self.keys.append(f2key)

    def set_params(self, params):
        '''
        установка параметров окна
        '''
        self.form.url = params['form_url']
        obj = params.get('object', None)
        if obj:
            self.form.from_object(obj)
        super(BaseEditWindow, self).set_params(params)

    def make_read_only(self, access_off=True, exclude_list=None):
        '''Управление состоянием Read-only окна'''
        super(BaseEditWindow, self).make_read_only(
            access_off, self._mro_exclude_list + (exclude_list or []))


#===============================================================================
# BaseListWindow
#===============================================================================
class BaseListWindow(BaseWindow):
    '''
    окно для отображения линейного справочника
    '''
    def _init_components(self):
        '''
        создание компонентов
        '''
        self.grid = ext.ExtObjectGrid()
        self.grid_filters = {}
        self.close_btn = self.btn_close = ext.ExtButton(
            name='close_btn',
            text=u'Закрыть',
            handler='function(){Ext.getCmp("%s").close();}' % self.client_id
        )
        self._mro_exclude_list.append(self.close_btn)

    def _do_layout(self):
        '''
        растановка компонентов
        '''
        self.maximizable = True
        self.minimizable = True
        self.layout = 'fit'
        self.items.append(self.grid)

        self.buttons.append(self.btn_close)

    def set_params(self, params):
        '''
        установка параметров окна
        '''
        assert 'pack' in params, 'incorrect params'
        params['pack'].configure_grid(self.grid)

        self.title = params.pop('title')
        self.grid.row_id_name = params['id_param_name']
        self.width = params['width']
        self.height = params['height']

    def add_grid_column_filter(self, column_name,
            filter_control=None, filter_name=None, tooltip=None):
        ''' Добавление фильтра к колонке'''
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
        ''' Удаление фильтра с колонки'''
        if not filter_name:
            filter_name = column_name
        if column_name in self.grid_filters:
            if filter_name in self.grid_filters[column_name]:
                del self.grid_filters[column_name][filter_name]
            if len(self.grid_filters[column_name]) == 0:
                del self.grid_filters[column_name]

    def render_filter(self, filter):
        lst = []
        if filter['filter_control']:
            return filter['filter_control']
        else:
            lst.append(u'xtype: "textfield"')
        if filter['tooltip']:
            lst.append(u'tooltip: "%s"' % filter['tooltip'])
        lst.append(u'filterName: "%s"' % filter['filter_name'])
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


#===============================================================================
# BaseSelectWindow
#===============================================================================
class BaseSelectWindow(BaseListWindow):
    '''
    окно выбора из линейного справочника
    '''
    column_name_on_select = 'name'

    def __init__(self, *args, **kwargs):
        super(BaseSelectWindow, self).__init__(*args, **kwargs)

    def _init_components(self):
        super(BaseSelectWindow, self)._init_components()
        self.grid.dblclick_handler = 'selectValue'
        self.select_btn = ext.ExtButton(
            handler='selectValue', text=u'Выбрать')
        self.buttons.insert(0, self.select_btn)
        self._mro_exclude_list.append(self.select_btn)

    def set_params(self, params):
        '''
        установка параметров окна
        '''
        super(BaseSelectWindow, self).set_params(params)
        self.template_globals = 'select-window.js'


#===============================================================================
# ColumnsConstructor
#===============================================================================
class ColumnsConstructor(object):
    '''
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
    '''

    class BandedCol(object):
        '''
        Группирующая колонка
        '''

        def __init__(self, items=None, **kwargs):
            '''
            items - подчинённые колонки
            **kwargs - передаются в конструктор ExtGridColumn
            '''
            self._column = ext.ExtGridColumn(**kwargs)
            self.items = list(items or [])


        def add(self, *args):
            '''
            Добавление колонок
            '''
            self.items.extend(args)


        def _cleaned(self):
            '''
            Возвращает элемент с очищенный от пустых подэлементов
            или None, если непустых подэлементов нет
            '''
            self.items = filter(None, [i._cleaned() for i in self.items])
            return self if self.items else None


        def _normalized_depth(self):
            '''
            Приведение всех подэлементов к одиному уровню вложенности
            Возвращается максимальная вложенность
            '''
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
            '''
            Вставка колонок. Возвращается кол-во вставленных колонок
            '''
            if is_top_level:
                if not self._cleaned(): return 0 # чистка
                level = self._normalized_depth() # нормализация уровней
            else:
                grid.add_banded_column(self._column, level, 0)

            if not self.items:
                return 0

            cnt = sum([i._populate(grid, level - 1) for i in self.items])
            self._column.colspan = cnt

            return cnt


    class Col(object):
        '''
        Простая колонка
        '''
        def __init__(self, **kwargs):
            self._column = ext.ExtGridColumn(**kwargs)

        def _cleaned(self):
            return self

        def _normalized_depth(self):
            return 1 # подэлементов нет, поэтому всегда вложенность 1

        def _populate(self, grid, level, is_top_level=False):
            grid.columns.append(self._column)
            return 1


    def __init__(self, items=None):
        self.items = list(items or [])


    def add(self, *args):
        '''
        Добавление колонок
        '''
        self.items.extend(args)


    def configure_grid(self, grid):
        '''
        Конфигурирование грида
        '''
        # все элементы суются в фейковую группирующую колонку,
        # которая отображаться не будет
        fake_col = self.BandedCol(items=self.items)
        fake_col._populate(grid, level=None, is_top_level=True)


#===============================================================================
# ModelEditWindow
#===============================================================================
class ModelEditWindow(BaseEditWindow):
    '''
    Простое окно редактирования модели
    '''
    # модель, для которой будет строится окно
    model = None

    # словарь kwargs для model_fields_to_controls ("field_list", и т.д.)
    field_fabric_params = None

    def _init_components(self):
        super(ModelEditWindow, self)._init_components()
        self._controls = model_fields_to_controls(
            self.model, self, **self.field_fabric_params)

    def _do_layout(self):
        super(ModelEditWindow, self)._do_layout()
        self.form.items.extend(map(anchor100, self._controls))

    @classmethod
    def fabricate(cls, model, **kwargs):
        '''
        Гененрирует класс-потомок для конкретной модели.
        Использование:
        class Pack(...):
            add_window = ModelEditWindow.fabricate(
                SomeModel,
                field_list=['code', 'name']
            )
        '''
        return type('%sEditWindow' % model.__name__, (cls,), {
            'model': model, 'field_fabric_params': kwargs})


#===============================================================================
def model_fields_to_controls(model, window,
        fields_prefix=None, field_list=[],
        exclude_list=[], **kwargs):
    '''
    Добавление на окно полей по полям модели,
    начинающимся с указанного префикса
    kwargs - передача доп параметров в конструктор элементов
    '''
    # ПОКА ВСЁ ОЧЕНЬ ПРИМИТИВНО
    # контроля перекрытия имен нет!
    exclude_prefixes = [x[:-1] for x in exclude_list if x.endswith('*')]
    exclude_list = [x for x in exclude_list if not x.endswith('*')]
    exclude_list += ['created', 'modified']
    controls = []

    if field_list:
        fields = map(model._meta.get_field, field_list)
    else:
        fields = model._meta.fields

    for f in fields:
        if fields_prefix and not f.name.startswith(fields_prefix): continue
        if exclude_list and f.name in exclude_list: continue
        if (exclude_prefixes and any((True for prefix in exclude_prefixes
                if f.name.startswith(prefix)))): continue

        try:
            ctl = _create_control_for_field(f, **kwargs)
        except GenerationError:
            continue

        setattr(window, 'field_%s' % f.name, ctl)
        controls.append(ctl)

    return controls


def _get_field_from_model(field_name, model):
    '''
    ищет поле по модели и создает котнро для него
    '''
    for f in model._meta.fields: #@UndefinedVariable
        if field_name in (f.name, f.attname):
            return f
    raise Exception(u'Не смогли найти поле %s в %s (был выбор из %s)' % (
        field_name, model, ','.join(map(lambda x:x.name, model._meta.fields))))


def _create_control_for_field_in_model(field_name, model, **kwargs):
    '''
    создает контроль для указнного поля из модели
    '''
    f = _get_field_from_model(field_name, model)
    return _create_control_for_field(f, **kwargs)


class GenerationError(Exception):
    '''
    ошибка возникает при проблемы генерации контрола
    '''
    pass


def _create_control_for_field(f, **kwargs):
    '''
    содает контроль для поля f = models.Field from model
    '''
    name = f.attname

    if f.choices:
        ctl = make_combo_box(data=list(f.choices), **kwargs)

    elif isinstance(f, django_models.BooleanField):
        ctl = ext.ExtCheckBox(**kwargs)

    elif isinstance(f, (
            django_models.CharField,
            django_models.TimeField, # время вводится в StringField
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
        ctl = ext.ExtDateField(**kwargs)

    elif isinstance(f, django_models.ForeignKey):
        ctl = _create_dict_select_field(f, **kwargs)

    elif isinstance(f, django_models.ImageField):
        ctl = ext.ExtImageUploadField(**kwargs)

    elif isinstance(f, django_models.FileField):
        ctl = ext.ExtFileUploadField(**kwargs)

    else:
        raise GenerationError(u'Не могу сгенирировать контрол для %s' % f)

    ctl.name = name
    ctl.label = f.verbose_name
    ctl.allow_blank = f.blank
    return ctl


def _create_dict_select_field(f, **kwargs):
    '''
    создает dictselectfield по заданному полю
    '''
    related_model = f.rel.to.__name__
    pack = m3_urls.get_pack(related_model)
    assert pack, 'Cant find pack for field %s (realated model %s)' % (
        f.name, related_model)

    params = {
        'display_field': pack.column_name_on_select,
        'value_field': 'id',
        'hide_edit_trigger': True,
        'hide_trigger': pack.allow_paging,
        'hide_clear_trigger': not f.blank,
        'hide_dict_select_trigger': False,
        'editable': False,
    }
    params.update(kwargs)

    ctl = ext.ExtDictSelectField(**params)
    ctl.pack = pack
    return ctl


class ComboBoxWithStore(ext.ExtComboBox):
    '''
    Потомок m3-комбобокса со втроенным стором
    Контрол имеет два свойства:
        data - фиксированный стор вида ((id, name),....)
        url - url для динамической загрузки
    Установка любого из этих свойств конфигурирует стор контрола
    '''

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
    '''
    Создает и возвращает ExtComboBox
    '''
    params = dict(
        display_field='name',
        value_field='id',
        trigger_action_all=True,
        editable=False,
    )
    params.update(kwargs)
    return ComboBoxWithStore(**params)


#===============================================================================
def anchor100(ctl):
    '''
    Устанавливает anchor в 100% у контрола и восвращает его (контрол)
    Пример использования:
        controls = map(anchor100, controls)
    '''
    if not isinstance(ctl, django_models.DateField):
        tools.modify(ctl, anchor='100%')
    return ctl


allow_blank = lambda ctl: tools.modify(ctl, allow_blank=True)
allow_blank.__doc__ = '''
    Устанавливает allow_blank=True у контрола и восвращает его (контрол)
    Пример использования:
        controls = map(allow_blank, controls)
    '''

deny_blank = lambda ctl: tools.modify(ctl, allow_blank=False)
deny_blank.__doc__ = '''
    Устанавливает allow_blank=False у контрола и восвращает его (контрол)
    Пример использования:
        controls = map(allow_blank, controls)
    '''


class DictionaryModelEditWindow(ModelEditWindow):
    """docstring for DictionaryModelEditWindow"""
    pass
