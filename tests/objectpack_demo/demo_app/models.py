#coding: utf-8
"""
Модели
"""
import datetime

from django.db import models

import objectpack


#==============================================================================
# Person
#==============================================================================
class Person(models.Model):
    """
    Физическое лицо
    """
    GENDERS = (
        (0, u'Женский'),
        (1, u'Мужской')
    )

    name = models.CharField(
        u'Имя', max_length=50)
    surname = models.CharField(
        u'Фамилия', max_length=50)
    patronymic = models.CharField(
        u'Отчество', max_length=50)
    date_of_birth = models.DateField(
        u'Дата рождения',
        null=True,
        default=datetime.date.today
    )
    gender = models.SmallIntegerField(
        u'Пол',
        choices=GENDERS,
        default=GENDERS[1][0]
    )

    @property
    def fullname(self):
        return u' '.join((self.name, self.surname, self.patronymic))

    def __unicode__(self):
        return self.fullname

    class Meta:
        verbose_name = u'Физическое лицо'
        verbose_name_plural = u'Физические лица'


#==============================================================================
# FakeModel
#==============================================================================
class FakeModel(objectpack.VirtualModel):
    """
    Виртуальная модель со столбцами field1, field2,...
    """

    @classmethod
    def _get_ids(cls):
        return xrange(1, 12)

    def __init__(self, id_obj):
        self.id = id_obj
        for i in xrange(1, 12):
            setattr(self, 'field%s' % i, i <= id_obj)


#==============================================================================
# TreeNode
#==============================================================================
class TreeNode(objectpack.VirtualModel):
    """
    Виртуальная модель, представляющая собой дерево
    """

    class FakeParent(object):
        def __init__(self, i):
            self.id = i

    @classmethod
    def _get_ids(cls):
        data = [
            {
                'name': 'Кошачьи',
                'items': [
                    {
                        'name': 'Крупные',
                        'items': [
                            ('Лев', '"Бонифаций"'),
                            ('Тигр', '"Шерхан"'),
                        ],
                    },
                    ('Кот', '"Матроскин"'),
                ],
            },
            ('Собака', '"Дружок"')
        ]

        def make_id(cnt=[0]):
            cnt[0] += 1
            return cnt[0]

        def walk(parent, items):
            for i in items:
                if isinstance(i, tuple):
                    yield {
                        'id': make_id(),
                        'parent': parent,
                        'kind': i[0],
                        'name': i[1],
                        'leaf': True
                    }
                else:
                    new_parent = make_id()
                    yield {
                        'id': new_parent,
                        'parent': parent,
                        'kind': i['name'],
                    }
                    for j in walk(new_parent, i['items']):
                        yield j

        result = list(walk(None, data))
        return result

    @property
    def is_leaf(self):
        return self._is_leaf

    def __init__(self, params):
        self.id = params['id']
        self.kind = params.get('kind')
        self.name = params.get('name')
        self._is_leaf = params.get('leaf', False)
        self.parent = self.FakeParent(params['parent'])

    class _meta:
        verbose_name = u"Дерево"
        verbose_name_plural = u"Дерево"
