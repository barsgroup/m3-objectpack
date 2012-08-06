#coding:utf-8
'''
File: controller.py
Author: Rinat F Sabitov
Description:
'''

from m3.ui import actions as m3_actions
from objectpack import observer


# Наблюдатель
obs = observer.Observer()


action_controller = observer.ObservableController(obs, "/actions")


@obs.subscribe
class Listener(object):

    listen = ['foo']

    def after(self, request, context, response):
        # подмена заголовка окна
        response.data.title = u'Му-ха-ха!'
