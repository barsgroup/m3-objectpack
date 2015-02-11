# coding:utf-8
from functools import partial

from m3 import actions as m3_actions

import objectpack
from objectpack import tree_object_pack
from objectpack.filters import FilterByField, ColumnFilterEngine

import models
import ui


# =============================================================================
# PersonObjectPack
# =============================================================================
class PersonObjectPack(objectpack.ObjectPack):
    """
    ObjectPack для модели Person
    """

    model = models.Person
    add_to_desktop = True
    add_to_menu = True

    edit_window = add_window = objectpack.ui.ModelEditWindow.fabricate(model)

    columns = [
        {
            'data_index': 'fullname',
            'header': u'ФИО',
            'sortable': True,
            'sort_fields': ('name', 'surname'),
            'filter': {
                'type': 'string',
                'custom_field': ('name', 'surname')
            }
        },
        {
            'data_index': 'date_of_birth',
            'header': u'Дата рождения',
            'filter': {
                'type': 'date'
            }
        },
        {
            'data_index': 'gender',
            'header': u'Пол',
            'filter': {
                'type': 'list',
                'options': models.Person.GENDERS
            }
        }
    ]


# =============================================================================
# CFPersonObjectPack
# =============================================================================
class CFPersonObjectPack(objectpack.ObjectPack):
    """
    Пак физ.лиц, демонстрирующий использование колоночных фильтров
    """
    title = u'Физические лица (колоночные фильтры)'

    model = models.Person
    _is_primary_for_model = False

    add_to_desktop = True
    add_to_menu = True

    filter_engine_clz = ColumnFilterEngine

    F = partial(FilterByField, model)

    columns = [
        {
            'data_index': 'fullname',
            'header': u'ФИО',
            'sortable': True,
            'sort_fields': ('name', 'surname'),
            'filter': (
                F('name') & F('surname')
            )
        },
        {
            'data_index': 'date_of_birth',
            'header': u'Дата рождения',
            'filter': (
                F('date_of_birth', '%s__gte', tooltip=u'с') &
                F('date_of_birth', '%s__lte', tooltip=u'по')
            )
        },
        {
            'data_index': 'gender',
            'header': u'Пол',
            'filter': F('gender')
        }
    ]


# =============================================================================
# BandedColumnPack
# =============================================================================
class BandedColumnPack(objectpack.ObjectPack):
    """Демонстрация Banded Columns"""

    title = u'Группирующие колонки'

    model = models.FakeModel

    width, height = 600, 600
    allow_paging = False

    add_to_desktop = True
    add_to_menu = True

    # Колонка становится группирующей, если имеет параметр columns - список
    # вложенных колонок
    # Строим 11 уровней колонок
    columns = (lambda mk_col: [reduce(
        lambda d, c: {
            'header': u'Группа',
            'columns': [
                mk_col(c),
                d,
                mk_col(c),
            ]
        },
        xrange(2, 12),
        mk_col(1)
    )])(
        lambda idx: {
            'type': 'checkbox',
            'header': '%s' % idx,
            'data_index': 'field%s' % idx,
            'width': 25,
            'fixed': True,
            'filter': {'type': 'string'}
        }
    )


# =============================================================================
# TreePack
# =============================================================================
class TreePack(tree_object_pack.TreeObjectPack):
    """
    Пример пака для работы с моделью-деревом
    """
    model = models.TreeNode

    add_to_desktop = True

    columns = [
        {
            "data_index": "kind",
            "header": u"Вид",
            "searchable": True
        },
        {
            "data_index": "name",
            "header": u"Кличка"
        }
    ]


# =============================================================================
# Паки гаражей с инструментом и сотрудницами
# =============================================================================
class GaragePack(objectpack.ObjectPack):
    """
    Гаражи
    """
    model = models.Garage

    add_to_menu = True
    add_to_desktop = True

    add_window = objectpack.ModelEditWindow.fabricate(model)
    edit_window = ui.GarageEditWindow


class ToolPack(objectpack.SlavePack):
    """
    Инвентарь гаража
    """
    model = models.GarageTool

    parents = ['garage']

    add_window = edit_window = objectpack.ModelEditWindow.fabricate(
        model=model, field_list=('name',)
    )


class StaffPack(objectpack.SlavePack):
    """
    Сотрудники гаража
    """
    model = models.GarageStaff

    parents = ['garage']

    can_delete = True

    def __init__(self):
        super(StaffPack, self).__init__()

        self.save_staff_action = SaveStaffAction()
        self.select_person_action = SelectPersonAction()

        self.replace_action('new_window_action', self.select_person_action)
        self.actions.append(self.save_staff_action)


class ROStaffPack(objectpack.ObjectPack):
    """
    Сотрудники гаража для отображения на раб.столе
    Демонстрирует колоночные фильтры с лукапом вглубь
    """
    model = models.GarageStaff

    add_to_menu = add_to_desktop = True

    filter_engine_clz = ColumnFilterEngine

    F = partial(FilterByField, model)

    columns = [
        {
            'header': u'ФИО',
            'data_index': 'person',
            'filter': (
                F('person__name') & F('person__surname')
            )
        },
        {
            'header': u'Гараж',
            'data_index': 'garage',
            'filter': F('garage__name')
        },
    ]


class SelectPersonAction(objectpack.SelectorWindowAction):
    """
    Экшн отображения списка физ.лиц
    """
    def configure_action(self, request, context):
        self.callback_url = self.parent.save_staff_action.get_absolute_url()
        self.data_pack = self.parent._get_model_pack('Person')


class SaveStaffAction(objectpack.BaseAction):
    """
    Экшн прикрепления физ.лиц к гаражу
    """
    url = r'/save_staff$'

    def run(self, request, context):
        ids = objectpack.extract_int_list(request, 'id')
        for i in ids:
            obj = models.GarageStaff(person_id=i)
            self.parent.save_row(obj, True, request, context)
        return m3_actions.OperationResult()
