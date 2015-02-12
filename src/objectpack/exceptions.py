# -*- coding: utf-8 -*-
"""
Классы исключений, обрабатываемых ObjectPack
"""


class OverlapError(Exception):
    """
    Исключние пересечения интервальных моделей
    """
    def __init__(self, objects, header=(
            u'Имеются пересечения со следующими записями:')):
        assert objects, u"Не указаны объекты, с которыми произошло пересечение"
        self._header = header
        self._objects = objects

    def __str__(self):
        return unicode(self)

    def __unicode__(self):
        return u'\n- '.join([self._header] + map(unicode, self._objects))


class ValidationError(Exception):
    """
    Исключение валидации
    """
    def __init__(self, text):
        assert text, u'Не указан текст сообщения'
        self._text = text

    def __str__(self):
        return unicode(self)

    def __unicode__(self):
        return unicode(self._text)
