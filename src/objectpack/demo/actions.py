# coding:utf-8
from functools import partial

from m3 import actions as m3_actions

import objectpack
from objectpack import tree_object_pack
from objectpack.filters import FilterByField, ColumnFilterEngine
from objectpack.demo.controller import obs

import objectpack.demo.models as models
import objectpack.demo.ui as ui


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

    edit_window = add_window = objectpack.ui.ModelEditWindow.fabricate(
        model, model_register=obs
    )

    columns = [
        {
            'data_index': '__unicode__',
            'hidden': True
        },
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
            "searchable": True,
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


class PersonCardObjectPack(PersonObjectPack):

    add_to_desktop = True
    add_to_menu = True

    model = models.PersonCard

    edit_window = add_window = ui.PersonCardEditWindow

    columns = [
        {
            'data_index': 'person.__unicode__',
            'header': u'ФИО',
        },
    ]

    serialization_rules = ([], ['*mother_id', '*father_id'])


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
class GarageMDWindowAction(objectpack.actions.MasterDetailWindowAction):

    @property
    def detail_pack(self):
        return self.parent._get_model_pack('GarageTool')

    def set_window_params(self):
        super(GarageMDWindowAction, self).set_window_params()
        self.win_params.update({
            'title': self.parent.title,
            'width': 600,
            'height': 400,
        })


class GaragePack(objectpack.ObjectPack):
    """
    Гаражи
    """
    model = models.Garage

    add_to_menu = True
    add_to_desktop = True

    add_window = objectpack.ModelEditWindow.fabricate(model)
    edit_window = ui.GarageEditWindow

    def __init__(self):
        super(GaragePack, self).__init__()
        self.md_window_action = GarageMDWindowAction()
        self.actions.append(self.md_window_action)

    def extend_desktop(self, desk):
        return [
            desk.Item(self.title, pack=self.list_window_action),
            desk.Item(self.title + '(MD)', pack=self.md_window_action),
        ]


class ToolPack(objectpack.SlavePack):
    """
    Инвентарь гаража
    """
    model = models.GarageTool

    _is_primary_for_model = True

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
