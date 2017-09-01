import pymongo

from barin import schema as S


# TODO: test backref logic


class InstanceManager(object):

    def __init__(self, manager, obj):
        self._manager = manager
        self._obj = obj

    def __getattr__(self, name):
        return getattr(self._manager, name)

    def synchronize(self, isdel=False):
        '''Sync all backrefs'''
        _id = self._obj['_id']
        for fname, f in self.fields.items():
            if f.backref:
                v = f.__get__(self._obj)
                other_cls = self.metadata[f.backref.cname]
                other_fld = other_cls.m.fields[f.backref.fname]
                if isinstance(f._schema, S.Array):
                    if isinstance(other_fld._schema, S.Array):
                        self._sync_m2m(_id, f, v, other_cls, other_fld, isdel)
                    else:
                        self._sync_o2m(_id, f, v, other_cls, other_fld, isdel)
                else:
                    if isinstance(other_fld._schema, S.Array):
                        self._sync_m2o(_id, f, v, other_cls, other_fld, isdel)
                    else:
                        self._sync_o2o(_id, f, v, other_cls, other_fld, isdel)

    def insert(self):
        return self._manager.insert_one(self._obj)

    def delete(self):
        return self._manager.delete_one(
            {'_id': self._obj._id})

    def replace(self, **kwargs):
        return self._manager.replace_one(
            {'_id': self._obj._id}, self._obj, **kwargs)

    def update(self, update_spec, **kwargs):
        refresh = kwargs.pop('refresh', False)
        if refresh:
            obj = self._manager.find_one_and_update(
                {'_id': self._obj._id},
                update_spec,
                return_document=pymongo.ReturnDocument.AFTER,
                **kwargs)
            if obj:
                self._obj.clear()
                self._obj.update(obj)
            else:
                # Object has been deleted
                return None
        else:
            return self._manager.update_one(
                {'_id': self._obj._id},
                update_spec, **kwargs)

    def _sync_m2m(self, this_id, this_fld, this_val, other_cls, other_fld, isdel):
        "this is an array, other is an array"
        q = (other_cls.m.query
            .match(other_fld == this_id)
            .match(other_cls._id.nin(this_val)))
        q.update_many(other_fld.pull(this_id))
        if isdel:
            return
        q = (other_cls.m.query
            .match(other_cls._id.in_(this_val)))
        q.update_many(other_fld.add_to_set(this_id))

    def _sync_o2m(self, this_id, this_fld, this_val, other_cls, other_fld, isdel):
        "this is an array, other is a scalar"
        q = (other_cls.m.query
            .match(other_fld == this_id)
            .match(other_cls._id.nin(this_val)))
        q.update_many(other_fld.set(None))
        if isdel:
            return
        q = (other_cls.m.query
            .match(other_cls._id.in_(this_val)))
        q.update_many(other_fld.set(this_id))

    def _sync_m2o(self, this_id, this_fld, this_val, other_cls, other_fld, isdel):
        "this is a scalar, other is an array"
        q = (other_cls.m.query
            .match(other_fld == this_id)
            .match(other_cls._id != this_val))
        q.update_many(other_fld.pull(this_id))
        if isdel:
            return
        q = (other_cls.m.query
            .match(other_cls._id == this_val))
        q.update_one(other_fld.add_to_set(this_id))

    def _sync_o2o(self, this_id, this_fld, this_val, other_cls, other_fld, isdel):
        "this is a scalar, other is a scalar"
        q = (other_cls.m.query
            .match(other_fld == this_id)
            .match(other_cls._id != this_val))
        q.update_many(other_fld.set(None))
        if isdel:
            return
        q = (other_cls.m.query
            .match(other_cls._id == this_val))
        q.update_one(other_fld.set(this_id))

