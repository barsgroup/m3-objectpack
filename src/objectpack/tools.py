#coding: utf-8
"""
Created on 23.07.2012
@author: pirogov
"""
import datetime
from functools import wraps

from django.db import transaction


#==============================================================================
# QuerySplitter
#==============================================================================
class QuerySplitter(object):
    """
    Порционный загрузчик выборки в итеративном контексте
    TODO: придумать тест для покрытия Exception'ов
    >>> from django.test.client import RequestFactory
    >>> rf = RequestFactory()
    >>> request = rf.post('', {'start': 5, 'limit': 10})
    >>> QuerySplitter.make_rows(
    ...     query=range(50),
    ...     validator=lambda x: x % 2,
    ...     request=request)
    [5, 7, 9, 11, 13, 15, 17, 19, 21, 23]
    """

    def __init__(self, query, start, limit=0):
        """
        query - выборка, start и limit - откуда и сколько отрезать.
        """
        self._data = query
        self._start = start
        self._limit = limit

        self._chunk = None
        self._cnt = 0

    def __iter__(self):
        if not self._limit:
            # перекрытие метода пропускания, заглушкой
            self.skip_last = lambda self: None
            return iter(self._data)
        return self

    def next(self):
        # если уже выдали нужное кол-во, останавливаем итерацию
        if self._cnt >= self._limit:
            raise StopIteration()

        # если порция кончилась, берем следующую
        if not self._chunk:
            self._chunk = list(
                self._data[self._start: self._start + self._limit])
            self._start += self._limit

        # отдаём порцию поэлементно
        if self._chunk:
            self._cnt += 1
            return self._chunk.pop(0)

        raise StopIteration()

    def skip_last(self):
        """
        Команда "не учитывать прошлое значение"
        """
        if not self._cnt:
            raise IndexError('Can`t skip any more!')
        self._cnt -= 1

    @classmethod
    def make_rows(
            cls, query,
            row_fabric=lambda item: item,
            validator=lambda item: True,
            request=None, start=0, limit=25):
        """
        Формирует список элементов для грида из выборки.
        Параметры листания берутся из request`а, или из параметров start/limit.
        Элементы перед попаданием прогоняются через row_fabric.
        В результирующий список попадают только те элементы,
        вызов validator для которых возвращает True.
        """
        if request:
            start = extract_int(request, 'start') or start
            limit = extract_int(request, 'limit') or limit

        query = cls(query, start, limit)

        rows = []
        for item in query:
            if validator(item):
                rows.append(row_fabric(item))
            else:
                query.skip_last()
        return rows


#==============================================================================
# ModelCache
#==============================================================================
class ModelCache(object):
    """
    Кэш get-ов объектов одной модели.
    В качестве ключа кэша - набор параметров для get-а
    Если в конструкторе указана фабрика объектов, то отсутствующие объекты
    создаются передачей аргументов фабрике.
    """

    def __init__(self, model, object_fabric=None):
        self._model = model
        self.MultipleObjectsReturned = model.MultipleObjectsReturned
        self._cache = {}
        self._last_kwargs = {}
        self._fabric = object_fabric

    @staticmethod
    def _key_for_dict(d):
        return tuple(sorted(d.iteritems(), key=lambda i: i[0]))

    def _get_object(self, kwargs):
        try:
            return self._model.objects.get(**kwargs)
        except self._model.DoesNotExist:
            return None

    def get(self, **kwargs):
        self._last_kwargs = kwargs

        key = self._key_for_dict(kwargs)

        if key in self._cache:
            return self._cache[key]

        new = self._get_object(kwargs)

        if new is None and self._fabric:
            new = self._fabric(**kwargs)
            assert isinstance(new, self._model)
            assert not new.id is None

        self._cache[key] = new

        return new

    def forget_last(self):
        if self._last_kwargs:
            key = self._key_for_dict(self._last_kwargs)
            self._cache.pop(key, None)


#==============================================================================
# TransactionCM
#==============================================================================
class TransactionCM(object):
    """
    Транизакция в виде ContextManager
    """
    def __init__(self, using=None, catcher=None):
        """
        using - DB alias
        catcher - внешний обработчик исключений
        """
        self._using = using
        self._catcher = catcher or self._default_catcher

    def __enter__(self):
        transaction.enter_transaction_management(True, self._using)
        return transaction

    def __exit__(self, *args):
        result = self._catcher(*args)
        if result:
            transaction.commit(self._using)
        else:
            transaction.rollback(self._using)
        return result

    @staticmethod
    def _default_catcher(ex_type, ex_inst, traceback):
        """
        Обработчик исключений, используемый по-умолчанию
        """
        return ex_type is None


def extract_int(request, key):
    """
    Нормальный извлекатель списка чисел
    >>> from django.test.client import RequestFactory
    >>> rf = RequestFactory()
    >>> request = rf.post('', {})
    >>> extract_int(request, 'NaN')

    >>> request = rf.post('', {'int':1})
    >>> extract_int(request, 'int')
    1
    """
    try:
        return int(request.REQUEST.get(key, ''))
    except ValueError:
        return None


def extract_int_list(request, key):
    """
    Нормальный извлекатель списка чисел
    >>> from django.test.client import RequestFactory
    >>> rf = RequestFactory()
    >>> request = rf.post('', {})
    >>> extract_int_list(request, 'list')
    []
    >>> request = rf.post('', {'list':'1,2,3,4'})
    >>> extract_int_list(request, 'list')
    [1, 2, 3, 4]
    """
    return map(int, filter(None, request.REQUEST.get(key, '').split(',')))


def str_to_date(s):
    """
    Извлечение даты из строки
    >>> str_to_date('31.12.2012') == str_to_date('2012-12-31, Happy New Year')
    True
    """
    if s:
        s = s[:10]
        s = s.replace('-', '.')
        try:
            s = datetime.datetime.strptime(s, '%d.%m.%Y')
        except ValueError:
            try:
                s = datetime.datetime.strptime(s, '%Y.%m.%d')
            except ValueError:
                s = None
    else:
        s = None
    return s


def extract_date(request, key, as_date=False):
    """
    Извлечение даты из request`а в формате DD.MM.YYYY
    (в таком виде приходит от ExtDateField)
    и приведение к Django-формату (YYYY-MM-DD)
    """
    res = str_to_date(request.REQUEST.get(key))
    if res and as_date:
        res = res.date()
    return res


def modify(obj, **kwargs):
    """
    Массовое дополнение атрибутов для объекта с его (объекта) возвратом
    >>> class Object(object): pass
    >>> cls = Object()
    >>> cls.param1 = 0
    >>> cls = modify(cls, **{'param1':1, })
    >>> cls.param1
    1
    """
    for attr, val in kwargs.iteritems():
        setattr(obj, attr, val)
    return obj


def modifier(**kwargs):
    """
    Принимает атрибуты со значениями (в виде kwargs)
    Возвращает модификатор - функцию, модифицирующую передаваемый ей объект
    указанными атрибутами.
    Пример:
        w10 = modifier(width=10)
        controls = map(w10, controls)
    >>> class Object(object): pass
    >>> w10 = modifier(width=10)
    >>> cls = w10(Object())
    >>> cls.width
    10
    """
    return lambda obj: modify(obj, **kwargs)


def find_element_by_type(container, cls):
    """
    посик экземлпяров элементов во всех вложенных контейнерах
    """
    res = []
    for item in container.items:
        if isinstance(item, cls):
            res.append(item)

        if hasattr(item, 'items'):
            res.extend(find_element_by_type(item, cls))
    return res


#==============================================================================
# collect_overlaps
#==============================================================================
def collect_overlaps(obj, queryset, attr_begin='begin', attr_end='end'):
    """
    Возвращает список объектов из указанной выборки, которые пересекаются
    с указанным объектом по указанным полям начала и конца интервала
    """
    obj_bgn = getattr(obj, attr_begin, None)
    obj_end = getattr(obj, attr_end, None)

    if obj_bgn is None or obj_end is None:
        raise ValueError(
            u'Объект интервальной модели должен иметь '
            u'непустые границы интервала!')

    if obj.id:
        queryset = queryset.exclude(id=obj.id)

    result = []
    for o in queryset.iterator():
        bgn = getattr(o, attr_begin, None)
        end = getattr(o, attr_end, None)
        if bgn is None or end is None:
            raise ValueError(
                u'Среди объектов выборки присутствуют некорректные!')

        def add():
            if any((
                bgn <= obj_bgn <= end,
                bgn <= obj_end <= end,
                obj_bgn <= bgn <= obj_end,
                obj_bgn <= end <= obj_end,
            )):
                result.append(o)

        try:
            add()
        except TypeError:
            if isinstance(obj_bgn, datetime.datetime) and isinstance(
                    obj_end, datetime.datetime):
                obj_bgn = obj_bgn.date()
                obj_end = obj_end.date()
                add()
    return result


#==============================================================================
# istraversable - проверка на "обходимость"
#==============================================================================
def istraversable(x):
    """
    возвращает True, если объект @x позволяет обход себя в цикле for
    """
    return (
        hasattr(x, '__iter__')
        or hasattr(x, '__next__')
        or hasattr(x, '__getitem__')
    )


#==============================================================================
# Кэширующий декоратор
#==============================================================================
def cached_to(attr_name):
    """
    Оборачивает простые методы (без аргументов) и property getters,
    с целью закэшировать первый полученный результат
    """
    def wrapper(fn):
        @wraps(fn)
        def inner(self):
            if hasattr(self, attr_name):
                result = getattr(self, attr_name)
            else:
                result = fn(self)
                setattr(self, attr_name, result)
            return result
        return inner
    return wrapper


#==============================================================================
# парсеры для декларации контекста
#==============================================================================
def int_or_zero(s):
    return 0 if not s else int(s)

def int_list(s):
    return [int(i.strip()) for i in s.split(',')]
