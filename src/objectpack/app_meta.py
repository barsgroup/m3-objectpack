# coding: utf-8
import os

from django.conf.urls import patterns


def register_urlpatterns():
    """
    Регистрация конфигурации урлов для приложения m3.contrib.users
    """
    return patterns(
        '',
        (r'^op_static/(?P<path>.*)$',
         'django.views.static.serve',
         {'document_root': os.path.join(
             os.path.dirname(__file__), 'static')}),
    )
