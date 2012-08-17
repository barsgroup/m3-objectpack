#coding:utf-8
"""
Виртуальная модель и proxy-обертка для работы с группой моделей
"""
import copy
from itertools import ifilter, islice, imap

from django.db.models import query, manager


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


#===============================================================================
# model_proxy_metaclass
#===============================================================================
def model_proxy_metaclass(name, bases, dic):
    """
    Метакласс для ModelProxy
    """
    model = dic.get('model')
    relations = dic.get('relations') or []

    if not model:
        return type(name, bases, dic)

    # сбор полей основной модели и указанных моделей, связанных с ней    
    def add_prefix(field, prefix):
        field = copy.copy(field)
        field.attname = '%s.%s' % (prefix, field.attname)
        return field

    def submeta(meta, path):
        for field in path.split('.'):
            meta = meta.get_field(field).related.parent_model._meta
        return meta

    meta = model._meta
    fields_ = []
    fields_dict = {}
    for prefix, meta in [(model.__name__.lower(), meta)] + [
            (rel, submeta(meta, rel)) for rel in relations]:
        for f in meta.fields:
            f = add_prefix(f, prefix)
            fields_.append(f)
            fields_dict[f.attname] = f


    # django-подобный класс метаинформации о модели
    class BaseMeta(object):
        fields = fields_

        verbose_name = model._meta.verbose_name
        verbose_name_plural = model._meta.verbose_name_plural

        @staticmethod
        def get_field(field_name):
            return fields_dict[field_name]

    meta_mixin = dic.pop('Meta', None)
    if meta_mixin:
        dic['_meta'] = type('_meta', (meta_mixin, BaseMeta), {})
    else:
        dic['_meta'] = BaseMeta


    relations_for_select = [r.replace('.', '__') for r in relations]

    # обёртка над QueryManager
    class WrappingManager(object):

        def __init__(self, manager, proxy=None):
            self._manager = manager
            self._proxy_cls = proxy
            self._query = None

        def _get_query(self):
            if not self._query:
                try:
                    self._query = self._manager._clone()
                except AttributeError:
                    self._query = self._manager
            return self._query.select_related(*relations_for_select)

        def __get__(self, inst, clz):
            if inst:
                raise TypeError(
                    "Manager can not be accessed from model instance!")
            return self.__class__(self._manager, clz)

        def __iter__(self):
            # при итерации по объектам выборки основной модели,
            # каждый объект оборачивается в Proxy
            for item in self._get_query():
                yield self._proxy_cls(item)

        def get(self, *args, **kwargs):
            return self._proxy_cls(self._get_query().get(*args, **kwargs))

        def iterator(self):
            return iter(self)

        def __getitem__(self, *args):
            return map(self._proxy_cls, self._get_query().__getitem__(*args))

        def __getattr__(self, attr):
            # все атрибуты, которые не перекрыты,
            # берутся в Manager`е базовой модели
            if attr in self.__dict__:
                return self.__dict__[attr]
            else:
                result = getattr(self._manager, attr)
                def wrapped(fn):
                    def inner(*args, **kwargs):
                        result = fn(*args, **kwargs)
                        if isinstance(result,
                                (manager.Manager, query.QuerySet)):
                            return self.__class__(result, self._proxy_cls)
                        return result
                    return inner
                if callable(result):
                    return wrapped(result)
                return result


    dic['objects'] = WrappingManager(model.objects)

    dic['DoesNotExist'] = model.DoesNotExist
    dic['MultipleObjectsReturned'] = model.MultipleObjectsReturned

    # создание класса Proxy
    proxy_class = type(name, bases, dic)

    return proxy_class


#===============================================================================
# ModelProxy
#===============================================================================
class ModelProxy(object):
    """
    Proxy-объект инкапсулирующий в себе несколько моделей
    (для случая, когда одна модель - основная, о другие - её поля)
    """
    __metaclass__ = model_proxy_metaclass

    model = None

    # список извлекаемых связанных моделей вида
    # ['relation', 'relation2.relation3']
    relations = None

    def __init__(self, obj=None):
        if obj is None:
            def wrap_save_method(child, parent, attr):
                old_save = child.save
                def inner(*args, **kwargs):
                    result = old_save(*args, **kwargs)
                    setattr(parent, attr, child.id)
                    return result
                return inner
            # если объект не указан - создается новый
            obj = self.model()
            # создаются экземпляры связанных объектов (вглубь)
            for path in self.relations:
                sub_obj, sub_model = obj, self.model
                for item in path.split('.'):
                    sub_model = sub_model._meta.get_field(
                        item).related.parent_model
                    new_sub_obj = sub_model()
                    # оборачивание save, для простановки xxx_id у род.модели
                    new_sub_obj.save = wrap_save_method(
                        new_sub_obj, sub_obj, '%s_id' % item)
                    # созданный объект, вкладывается в зависимый 
                    setattr(sub_obj, item, new_sub_obj)
                    # подъем на уровень выше
                    sub_obj = new_sub_obj
            self.id = None
        else:
            self.id = obj.id

        setattr(self, self.model.__name__.lower(), obj)
        # заполнение атрибутов proxy по заданным связям вглубь (xxx.yyy)
        def set_by_path(dest, src, steps):
            new_src = getattr(src, steps[0], None)
            setattr(dest, steps[0], new_src)
            if new_src and len(steps) > 1:
                set_by_path(src, new_src, steps[1:])
        for rel in self.relations:
            set_by_path(self, obj, rel.split('.'))

    def save(self):
        raise NotImplementedError()

    def safe_delete(self):
        raise NotImplementedError()
