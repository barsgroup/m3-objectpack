#coding:utf-8
'''
File: controller.py
Author: Rinat F Sabitov
Description:
'''

from m3.ui import actions as m3_actions
from objectpack import observer


def logger(msg):
    print "Observer: %s" % msg

# Наблюдатель
obs = observer.Observer(logger=logger, verbose_level=observer.Observer.LOG_MORE)


action_controller = observer.ObservableController(obs, "/actions")


@obs.subscribe
class Listener(object):

    listen = ['foo']

    def after(self, request, context, response):
        # подмена заголовка окна
        response.data.title = u'Му-ха-ха! (%s)' % self.action.__class__.__name__


@obs.subscribe
class StarToHash(object):

    listen = ['fakemodel/.*']

    def prepare_obj(self, obj):
        if obj.get('field1', None) == u'*':
            obj['field1'] = '#'
        return obj
