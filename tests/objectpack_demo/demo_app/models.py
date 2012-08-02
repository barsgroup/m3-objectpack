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
        return self
