#coding: utf-8
'''
File: models.py
Author: Rinat F Sabitov
Description:
'''
from django.db import models
from django.utils.translation import ugettext as _


class Person(models.Model):
    """docstring for Person"""
    pass

    class Meta:
        verbose_name = _(u'клиент')
        verbose_name_plural = _(u'клиенты')
