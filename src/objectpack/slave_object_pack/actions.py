#coding:utf-8
'''
@author: shibkov
'''

from m3.ui.actions import utils
from m3.helpers import urls

import objectpack


class SlavePack(objectpack.ObjectPack):
    '''
    "Ведомый" набор действий. Используется чаще всего для грида внутри
    окна редактирования объекта, отображающего объеты,
    связанные с редактируемым 
    '''

    # parents - список полей в модели которые должны браться из контекста
    # например: parents = ['employer', 'subject']
    parents = []

    __parents_cached = None
    @property
    def _parents(self):
        if self.__parents_cached:
            return self.__parents_cached
        result = self.__parents_cached = []
        for parent in self.parents:
            f = self.model._meta.get_field(parent)
            pack = urls.get_pack_instance(f.rel.to.__name__)
            result.append((
                pack.id_param_name,
                pack.title,
                parent
            ))
        return result


    def _get_parents_from_request(self, request, field_name_suffix=''):
        result = {}
        for id_param_name, title, field_name in self._parents: #@UnusedVariable
            parent_id = utils.extract_int(request, id_param_name)
            if not parent_id:
                raise ValueError(
                    u'Не указано ' + id_param_name)
            result[field_name + field_name_suffix] = parent_id
        return result


    def save_row(self, obj, create_new, request, context):
        obj.__dict__.update(
            self._get_parents_from_request(request, field_name_suffix='_id')
        )
        return super(SlavePack, self).save_row(
            obj, create_new, request, context)


    def get_rows_query(self, request, context):
        q = super(SlavePack, self).get_rows_query(request, context)
        try:
            q = q.filter(**self._get_parents_from_request(request))
        except ValueError:
            q = self.model.objects.none()
        return q


    # SlavePack обычно не является основным для модели
    _is_primary_for_model = False

