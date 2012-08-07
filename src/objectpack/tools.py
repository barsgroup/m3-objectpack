#coding: utf-8
'''
Created on 23.07.2012

@author: pirogov
'''
from itertools import ifilter, islice, imap

from django.db import transaction

#==============================================================================
# QuerySplitter
#==============================================================================
class QuerySplitter(object):
    '''
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
    '''

    def __init__(self, query, start, limit=0):
        '''
        query - выборка, start и limit - откуда и сколько отрезать.
        '''
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
        '''
        Команда "не учитывать прошлое значение"
        '''
        if not self._cnt:
            raise IndexError('Can`t skip any more!')
        self._cnt -= 1

    @classmethod
    def make_rows(cls, query,
            row_fabric=lambda item: item,
            validator=lambda item: True,
            request=None, start=0, limit=25):
        '''
        Формирует список элементов для грида из выборки.
        Параметры листания берутся из request`а, или из параметров start/limit.
        Элементы перед попаданием прогоняются через row_fabric.
        В результирующий список попадают только те элементы,
        вызов validator для которых возвращает True.
        '''
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
    '''
    Кэш get-ов объектов одной модели.
    В качестве ключа кэша - набор параметров для get-а
    '''

    def __init__(self, model):
        self._model = model
        self.MultipleObjectsReturned = model.MultipleObjectsReturned
        self._cache = {}
        self._last_kwargs = {}

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
        new = self._cache[key] = self._get_object(kwargs)
        return new

    def forget_last(self):
        if self._last_kwargs:
            key = self._key_for_dict(self._last_kwargs)
            self._cache.pop(key, None)


#==============================================================================
# TransactionCM
#==============================================================================
class TransactionCM(object):
    '''
    Транизакция в виде ContextManager
    '''
    def __init__(self, using=None, catcher=None):
        '''
        using - DB alias
        catcher - внешний обработчик исключений
        '''
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
        '''Обработчик исключений, используемый по-умолчанию'''
        return ex_type is None


def extract_int(request, key):
    '''
    Нормальный извлекатель списка чисел
    >>> from django.test.client import RequestFactory
    >>> rf = RequestFactory()
    >>> request = rf.post('', {})
    >>> extract_int(request, 'NaN')

    >>> request = rf.post('', {'int':1})
    >>> extract_int(request, 'int')
    1
    '''
    try:
        return int(request.REQUEST.get(key, ''))
    except ValueError:
        return None


def extract_int_list(request, key):
    '''
    Нормальный извлекатель списка чисел
    >>> from django.test.client import RequestFactory
    >>> rf = RequestFactory()
    >>> request = rf.post('', {})
    >>> extract_int_list(request, 'list')
    []
    >>> request = rf.post('', {'list':'1,2,3,4'})
    >>> extract_int_list(request, 'list')
    [1, 2, 3, 4]
    '''
    return map(int, filter(None, request.REQUEST.get(key, '').split(',')))


def modify(obj, **kwargs):
    '''
    Массовое дополнение атрибутов для объекта с его (объекта) возвратом
    >>> class Object(object): pass
    >>> cls = Object()
    >>> cls.param1 = 0
    >>> cls = modify(cls, **{'param1':1, })
    >>> cls.param1
    1
    '''
    for attr, val in kwargs.iteritems():
        setattr(obj, attr, val)
    return obj


def modifier(**kwargs):
    '''
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
    '''

    return lambda obj: modify(obj, **kwargs)


def find_element_by_type(container, cls):
    '''
    посик экземлпяров элементов во всех вложенных контейнерах
    '''
    res = []
    for item in container.items:
        if isinstance(item, cls):
            res.append(item)

        if hasattr(item, 'items'):
            res.extend(find_element_by_type(item, cls))
    return res


#===============================================================================
# VirtualModelManager
#===============================================================================
class VirtualModelManager(object):

    _operators = {
        'iexact': lambda val: lambda x, y = val.lower(): x.lower() == y,
        'icontains': lambda val: lambda x, y = val.lower(): y in x.lower(),
        'lte': lambda val: lambda x: x <= val,
        'gte': lambda val: lambda x: x >= val,
        'lt': lambda val: lambda x: x < val,
        'gt': lambda val: lambda x: x > val,
        'isnull': lambda val: lambda x: bool(x) == val,
    }

    def __init__(self, model_clz=None, procs=None, **kwargs):
        if not model_clz:
            return
        self._clz = model_clz
        self._procs = procs or []
        self._ids_getter_kwargs = kwargs

    def __get__(self, inst, clz):
        if inst:
            raise TypeError("Manager can not be accessed from model instance!")
        return self.__class__(clz)

    def all(self):
        return self._fork_with(self._procs[:])

    def __getitem__(self, arg):
        if isinstance(arg, slice):
            procs = self._procs[:]
            procs.append(
                lambda data: islice(data, arg.start, arg.stop, arg.step))
            return self._fork_with(procs)
        return list(self)[arg]

    def __iter__(self):
        return reduce(lambda arg, fn: fn(arg), self._procs,
            imap(self._clz._from_id, self._clz._get_ids(
                **self._ids_getter_kwargs)))

    def _fork_with(self, procs=None, **kwargs):
        kw = self._ids_getter_kwargs.copy()
        kw.update(kwargs)
        if not procs:
            procs = self._procs[:]
        return self.__class__(self._clz, procs, **kw)

    def configure(self, **kwargs):
        return self._fork_with(**kwargs)

    @classmethod
    def _make_getter(cls, key, val=None, allow_op=False):
        folder = lambda fn, attr: lambda obj: fn(getattr(obj, attr))
        default_op = lambda op: lambda val: lambda obj: val == getattr(obj, op)
        key = key.split('__')
        if allow_op:
            if len(key) > 1:
                op = key.pop()
                op = cls._operators.get(op, default_op(op))(val)
            else:
                op = (lambda val: lambda obj: obj == val)(val)
        else:
            op = lambda obj: obj
        return reduce(folder, reversed(key), op)

    def filter(self, **kwargs): #@ReservedAssignment
        procs = self._procs[:]
        if kwargs:
            fns = [self._make_getter(key, val, allow_op=True)
                for key, val in kwargs.iteritems()]
            procs.append(
                lambda items: ifilter(
                    lambda obj: all(fn(obj) for fn in fns), items))
        return self._fork_with(procs)

    def order_by(self, *args):
        procs = self._procs[:]
        if args:
            getters = map(self._make_getter, args)
            key_fn = lambda obj: tuple(g(obj) for g in getters)
            procs.append(lambda data: iter(sorted(data, key=key_fn)))
        return self._fork_with(procs)

    def get(self, *args, **kwargs):
        if not kwargs and args:
            kwargs['id'] = args[0]
        result = list(self.filter(**kwargs))
        if not result:
            raise self._clz.DoesNotExist()
        elif len(result) > 1:
            raise self._clz.MultipleObjectsReturned()
        return result[0]

    def select_related(self):
        return self

    def count(self):
        return len(list(self))


#===============================================================================
# VirtualModel
#===============================================================================
class VirtualModel(object):

    class DoesNotExist(Exception):
        pass

    class MultipleObjectsReturned(Exception):
        pass

    @classmethod
    def _get_ids(cls):
        return NotImplemented

    @classmethod
    def _from_id(cls, id_obj):
        return cls(id_obj)

    objects = VirtualModelManager()


def collect_overlaps(obj, queryset, attr_begin='begin', attr_end='end'):
    '''
    Возвращает список объектов из указанной выборки, которые пересекаются
    с указанным объектом по указанным полям начала и конца интервала
    '''
    obj_bgn = getattr(obj, attr_begin, None)
    obj_end = getattr(obj, attr_end, None)

    if obj_bgn is None or obj_end is None: raise ValueError(
        u'Объект интервальной модели должен иметь непустые границы интервала!')

    if obj.id: queryset = queryset.exclude(id=obj.id)

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
                )): result.append(o)

        try:
            add()
        except TypeError:
            if isinstance(obj_bgn, datetime.datetime) and isinstance(obj_end, datetime.datetime):
                obj_bgn = obj_bgn.date()
                obj_end = obj_end.date()
                add()
    return result
