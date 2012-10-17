# -*- coding: utf-8 -*-

from django.db import models


#-----------------------------------------------------------------------------
class Garage(models.Model):
    """
    Гараж
    """
    name = models.CharField(
        max_length=20,
        verbose_name=u'Наименование')

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = u'Гараж'
        verbose_name_plural = u'Гаражи'


#-----------------------------------------------------------------------------
class GarageStaff(models.Model):
    """
    Сотрудник гаража
    """
    garage = models.ForeignKey(
        Garage, verbose_name=u'Гараж')
    person = models.ForeignKey(
        'demo_app.Person')

    def __unicode__(self):
        return unicode(self.person)

    class Meta:
        verbose_name = u'Сотрудник гаража'
        verbose_name_plural = u'Сотрудники гаража'


#-----------------------------------------------------------------------------
class GarageTool(models.Model):
    """
    Гаражный инструмент
    """
    name = models.CharField(
        max_length=20,
        verbose_name=u'Наименование')

    garage = models.ForeignKey(
        Garage, verbose_name=u'Гараж')

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = verbose_name_plural = u'Гаражный инструмент'
