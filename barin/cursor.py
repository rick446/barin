class Cursor(object):

    def __init__(self, manager, pymongo_cursor):
        self._manager = manager
        self.pymongo_cursor = pymongo_cursor
        self._wrap_cursor('sort')
        self._wrap_cursor('skip')
        self._wrap_cursor('limit')

    def __getattr__(self, name):
        return getattr(self.pymongo_cursor, name)

    def __iter__(self):
        for obj in self.pymongo_cursor:
            yield self._manager.validate(obj)

    def all(self):
        return list(self)

    def first(self):
        return iter(self).next()

    def one(self):
        it = iter(self)
        res = it.next()
        try:
            it.next()
        except StopIteration:
            return res
        raise ValueError('More than one result returned for one()')

    def _wrap_cursor(self, name):
        def wrapper(*args, **kwargs):
            orig = getattr(self.pymongo_cursor, name)
            res = orig(*args, **kwargs)
            return Cursor(self._manager, res)
        wrapper.__name__ = 'wrapped_{}'.format(name)
        setattr(self, name, wrapper)
        return wrapper