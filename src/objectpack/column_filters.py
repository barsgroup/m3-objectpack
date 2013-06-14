# -*- coding: utf-8 -*-
"""
Фабрики фильтров для колонок гридов
"""
from django.db.models import Q
from django.utils.translation import ugettext as _


def choices(field, data):
    """
    Возвращает списковый фильтр для поля @field
    с указанными вариантами @data (Django model choices)
    """
    return {
        'type': 'list',
        'options': data,
    }


def yes_no(field):
    """
    Возвращает списковый фильтр
    с вариантами "Да"/"Нет" для boolean-поля @field
    """
    return choices(field, ((1, _(u'Да')), (0, _(u'Нет'))))


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
