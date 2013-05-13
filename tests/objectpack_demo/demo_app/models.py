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
