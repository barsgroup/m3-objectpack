# coding: utf-8
from __future__ import absolute_import

from datetime import date
from datetime import datetime
from datetime import time
from decimal import Decimal

from django.core.validators import MaxValueValidator
from django.core.validators import MinLengthValidator
from django.core.validators import MinValueValidator
from django.db import models


class TestModel(models.Model):

    int_field = models.IntegerField(
        validators=[
            MinValueValidator(-1000),
            MaxValueValidator(1000),
        ]
    )
    pint_field = models.PositiveIntegerField(
        validators=[
            MaxValueValidator(200),
        ]
    )
    psint_field = models.PositiveIntegerField(
        validators=[
            MaxValueValidator(400),
        ]
    )
    choices_field = models.PositiveSmallIntegerField(
        choices=(
            (1, u'Раз'),
            (2, u'Два'),
            (3, u'Три'),
            (4, u'Четыре'),
            (5, u'Пять'),
        ),
        validators=[
            MinLengthValidator(1),
            MaxValueValidator(2),
        ]
    )
    float_field = models.FloatField(
        validators=[
            MinValueValidator(-10.5),
            MaxValueValidator(10.5),
        ]
    )
    decimal_field = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        validators=[
            MinValueValidator(Decimal('-5.5')),
            MaxValueValidator(Decimal('5.5')),
        ]
    )
    date_field = models.DateField(
        validators=[
            MinValueValidator(date(2000, 1, 1)),
            MaxValueValidator(date(2000, 12, 31)),
        ]
    )
    time_field = models.TimeField(
        validators=[
            MinValueValidator(time(10)),
            MaxValueValidator(time(12)),
        ]
    )
    datetime_field = models.DateTimeField(
        validators=[
            MinValueValidator(datetime(2010, 1, 1, 10)),
            MaxValueValidator(datetime(2010, 1, 1, 12)),
        ]
    )
    char_field = models.CharField(
        max_length=10,
        validators=[
            MinLengthValidator(3),
        ]
    )
    text_field = models.TextField(
        max_length=100,
        validators=[
            MinLengthValidator(50),
        ]
    )

    class Meta:
        app_label = 'testapp'
