# coding:utf-8
"""
Механизм подписки на события, возникающие при выполнении actions
"""

from base import (
    ACTION_NAME_ATTR,

    ObservableMixin,
    Observer,
    ObservableController
)

from tools import name_action
