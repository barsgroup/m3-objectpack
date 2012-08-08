#coding: utf-8
'''
File: actions.py
Author: Rinat F Sabitov
Description:
'''

import objectpack

from m3.ui.ext import all_components as ext
import ui

class TreeObjectPack(objectpack.ObjectPack):
    """docstring for TreeObjectPack"""

    list_window = ui.BaseTreeListWindow # Форма списка
    select_window = ui.BaseTreeSelectWindow # Форма выбора @UndefinedVariable


