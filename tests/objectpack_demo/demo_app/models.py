#coding: utf-8
'''
File: models.py
Author: Rinat F Sabitov
Description:
'''
from django.db import models
from django.utils.translation import ugettext as _

import objectpack


#===============================================================================
# Person
#===============================================================================
class Person(models.Model):
    """docstring for Person"""

    name = models.CharField(u'имя', max_length=50)
    surname = models.CharField(u'фамилия', max_length=50)
    patronymic = models.CharField(u'отчество', max_length=50)
    date_of_birth = models.DateField(u'дата рождения', null=True)

    def fullname(self):
        """docstring for fullname"""
        return self.name, self.surname, self.patronymic

    def __unicode__(self):
        return self.fullname

    class Meta:
        verbose_name = _(u'клиент')
        verbose_name_plural = _(u'клиенты')


#===============================================================================
# FakeModel
#===============================================================================
class FakeModel(objectpack.VirtualModel):
    """Виртуальная модель со столбцами field1, field2,..."""

    @classmethod
    def _get_ids(cls):
        return xrange(1, 12)

    @classmethod
    def _from_id(cls, id_obj):
        self = cls()
        self.id = id_obj
        for i in xrange(1, 12):
            setattr(self, 'field%s' % i, ['', '*'][i == id_obj])
            setattr(self, 'field%s' % i, ['', '*'][i <= id_obj])
        return self
