# coding: utf-8
from __future__ import absolute_import

from datetime import date
from datetime import time
from decimal import Decimal

from django.test import SimpleTestCase
from m3_ext.ui.fields.simple import ExtDateField
from m3_ext.ui.fields.simple import ExtNumberField
from m3_ext.ui.fields.simple import ExtStringField
from m3_ext.ui.fields.simple import ExtTextArea
from m3_ext.ui.fields.simple import ExtTimeField
import six

from objectpack.models import VirtualModel
from objectpack.tools import copy_columns
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

        # Для комбобоксов не должно быть валидации по длине поля, т.к.
        # проверяется длина отображаемого текста, а не значения.
        self.assertTrue(control.min_length is None)
        self.assertTrue(control.max_length is None)

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


class VirtualModelTestCase(SimpleTestCase):

    """Тесты для VirtualModel."""

    def setUp(self):
        self.data = {'1': 'first', '2': 'second', '3': 'third'}
        self.TestVirtualModel = VirtualModel.from_data(
            [
                {'id': idx, 'name': name} for idx, name in
                six.iteritems(self.data)
            ],
            class_name='TestVirtualModel'
        )

    def test_values(self):
        data = [
            {'id': idx, 'name': name} for idx, name in
            six.iteritems(self.data)
        ]
        result = self.TestVirtualModel.objects.values('id', 'name')
        self.assertEqual(
            first=data,
            second=list(result)
        )

    def test_values_list_with_single_field(self):
        result = self.TestVirtualModel.objects.values_list('id', flat=True)
        self.assertEqual(['1', '2', '3'], sorted(result))

    def test_values_list_with_multi_fields(self):
        with self.assertRaises(TypeError):
            self.TestVirtualModel.objects.values_list('id', 'name', flat=True)

        result = self.TestVirtualModel.objects.values_list('id', 'name')
        self.assertEqual(
            first=list(six.iteritems(self.data)),
            second=list(result)
        )


class ToolsTestCase(SimpleTestCase):

    """Тесты для инструментария из objectpack.tools."""

    def test__copy_columns(self):
        base_columns = (
            dict(
                data_index='number',
                width=1,
            ),
            dict(
                data_index='code',
                header='Код',
                width=2,
            ),
            dict(
                data_index='name',
                width=4,
            ),
        )

        columns = copy_columns(
            base_columns,
            dict(
                data_index='start_date',
                width=100,
                fixed=True,
            ),
            'code',
            dict(
                data_index='name',
                title='Наименование',
                width=5,
            ),
            code=dict(
                width=100,
                fixed=True,
            ),
        )

        target_columns = (
            dict(
                data_index='start_date',
                width=100,
                fixed=True,
            ),
            dict(
                data_index='code',
                header='Код',
                width=100,
                fixed=True,
            ),
            dict(
                data_index='name',
                title='Наименование',
                width=5,
            ),
        )

        self.assertEqual(columns, target_columns)
