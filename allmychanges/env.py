class Environment(object):
    def __init__(self, parent=None):
        self.__dict__['_parent'] = parent
        self.__dict__['_data'] = {}

    def __getattr__(self, name):
        if name in self._data:
            return self._data[name]
        else:
            if self._parent is None:
                raise AttributeError('Attribute {0} does not exist'.format(name))
            else:
                return getattr(self._parent, name)

    def __setattr__(self, name, value):
        self._data[name] = value

    def __eq__(self, other):
        undefined = object()
        return all(getattr(self, key) == getattr(other, key, undefined)
                   for key in self.keys())

    def __repr__(self, only=None):
        attrs = [(key, getattr(self, key))
                 for key in self.keys()]

        if only is not None:
            only = dict(key
                        if isinstance(key, tuple)
                        else (key, lambda text: text)
                        for key in only)
            attrs = [(key, only[key](value))
                     for key, value in attrs
                     if key in only]

        attrs = map(u'{0[0]}={0[1]}'.format, attrs)
        return u'<{0} {1}>'.format(
            getattr(self, 'type', 'unknown'), ', '.join(attrs))

    def push(self, **kwargs):
        new_env = Environment(self)
        for key, value in kwargs.items():
            setattr(new_env, key, value)
        return new_env

    def keys(self):
        result = self._data.keys()
        if self._parent is not None:
            result += self._parent.keys()
        result = list(set(result))
        result.sort()
        return result
