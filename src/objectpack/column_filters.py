# -*- coding: utf-8 -*-
"""
Фабрики фильтров для колонок гридов
"""
from django.db.models import Q
from django.utils.translation import ugettext as _


def choices(field, choices):
    """
    Возвращает списковый фильтр для поля @field
    с указанными вариантами @choices
    """
    def callback(val):
        filt = Q()
        for k, v in choices:
            if k in val:
                filt |= Q(**{field: v})
        return filt
    return {
        'type': 'list',
        'options': [ch[0] for ch in choices],
        'custom_field': callback
    }


def yes_no(field):
    """
    Возвращает списковый фильтр
    с вариантами "Да"/"Нет" для boolean-поля @field
    """
    return choices(field, ((_(u'Да'), True), (_(u'Нет'), False)))


def within(field_from, field_to):
    """
    Возвращает фильтр, проверяющий попадание указанного значения
    в диапазон, ограниченный значениями полей @field_from, @field_to
    """
    return {
        'type': 'string',
        'custom_field': lambda val: Q(**{
            '%s__lte' % field_from: val,
            '%s__gte' % field_to: val,
        })
    }
