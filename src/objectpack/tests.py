#coding: utf-8
"""
File: tests.py
Author: Rinat F Sabitov
Description:
"""

from django.test import TestCase
import tools
import unittest
import doctest

class MainTest(TestCase):

    def test_workspace(self):
        pass

def suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite(tools))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(MainTest))
    return suite
