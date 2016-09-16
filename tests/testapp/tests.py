# coding: utf-8
from datetime import date
from datetime import time
from decimal import Decimal

from django.test import SimpleTestCase
from m3_ext.ui.fields.simple import ExtDateField
from m3_ext.ui.fields.simple import ExtNumberField
from m3_ext.ui.fields.simple import ExtStringField
from m3_ext.ui.fields.simple import ExtTextArea
from m3_ext.ui.fields.simple import ExtTimeField

from objectpack.ui import ComboBoxWithStore
from objectpack.ui import _create_control_for_field

from .models import TestModel


class CreateControlForFieldTestCase(SimpleTestCase):

    u"""Проверка функции _create_control_for_field."""

    def test_integer_fields(self):
        u"""Проверка генерации контролов для целочисленных полей."""
        control = _create_control_for_field(
            TestModel._meta.get_field('int_field')
        )
        self.assertIsInstance(control, ExtNumberField)
        self.assertTrue(control.allow_negative)
        self.assertFalse(control.allow_decimals)
        self.assertEquals(control.min_value, -1000)
        self.assertEquals(control.max_value, 1000)
        # ---------------------------------------------------------------------
        control = _create_control_for_field(
            TestModel._meta.get_field('pint_field')
        )
        self.assertIsInstance(control, ExtNumberField)
        self.assertFalse(control.allow_negative)
        self.assertFalse(control.allow_decimals)
        self.assertEquals(control.max_value, 200)
        # ---------------------------------------------------------------------
        control = _create_control_for_field(
            TestModel._meta.get_field('psint_field')
        )
        self.assertIsInstance(control, ExtNumberField)
        self.assertFalse(control.allow_negative)
        self.assertFalse(control.allow_decimals)
        self.assertEquals(control.max_value, 400)

    def test_choices_fields(self):
        u"""Проверка генерации контролов для целочисленных полей."""
        field = TestModel._meta.get_field('choices_field')
        control = _create_control_for_field(field)
        self.assertIsInstance(control, ComboBoxWithStore)
        self.assertEquals(set(control.data), set(field.choices))

    def test_float_field(self):
        u"""Проверка контрола для поля ввода вещественных чисел."""
        control = _create_control_for_field(
            TestModel._meta.get_field('float_field')
        )
        self.assertIsInstance(control, ExtNumberField)
        self.assertTrue(control.allow_negative)
        self.assertTrue(control.allow_decimals)
        self.assertEquals(control.min_value, -10.5)
        self.assertEquals(control.max_value, 10.5)

    def test_decimal_field(self):
        u"""Проверка контрола для поля ввода вещественных чисел."""
        control = _create_control_for_field(
            TestModel._meta.get_field('decimal_field')
        )
        self.assertIsInstance(control, ExtNumberField)
        self.assertTrue(control.allow_negative)
        self.assertTrue(control.allow_decimals)
        self.assertEquals(control.min_value, Decimal('-5.5'))
        self.assertEquals(control.max_value, Decimal('5.5'))

    def test_datetime_fields(self):
        u"""Проверка контрола для поля ввода даты/времени."""
        control = _create_control_for_field(
            TestModel._meta.get_field('date_field')
        )
        self.assertIsInstance(control, ExtDateField)
        self.assertEquals(control.min_value, date(2000, 1, 1))
        self.assertEquals(control.max_value, date(2000, 12, 31))
        # ---------------------------------------------------------------------
        control = _create_control_for_field(
            TestModel._meta.get_field('datetime_field')
        )
        self.assertIsInstance(control, ExtDateField)
        self.assertEquals(control.min_value, date(2010, 1, 1))
        self.assertEquals(control.max_value, date(2010, 1, 1))
        # ---------------------------------------------------------------------
        control = _create_control_for_field(
            TestModel._meta.get_field('time_field')
        )
        self.assertIsInstance(control, ExtTimeField)
        self.assertEquals(control.min_value, time(10))
        self.assertEquals(control.max_value, time(12))

    def test_text_fields(self):
        u"""Проверка контрола для поля ввода даты/времени."""
        control = _create_control_for_field(
            TestModel._meta.get_field('char_field')
        )
        self.assertIsInstance(control, ExtStringField)
        self.assertEquals(control.min_length, 3)
        self.assertEquals(control.max_length, 10)
        # ---------------------------------------------------------------------
        control = _create_control_for_field(
            TestModel._meta.get_field('text_field')
        )
        self.assertIsInstance(control, ExtTextArea)
        self.assertEquals(control.min_length, 50)
        self.assertEquals(control.max_length, 100)
