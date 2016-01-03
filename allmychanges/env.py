import weakref
import anyjson
import arrow


class Environment(object):
    def __init__(self, _parent=None, **kwargs):
        self.__dict__['_parent'] = _parent
        self.__dict__['_children'] = []
        self.__dict__['_data'] = kwargs.copy()

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
        return len(self.keys()) == len(other.keys()) \
            and all(getattr(self, key) == getattr(other, key, undefined)
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
            getattr(self, 'type', 'unknown'), u', '.join(attrs)) \
            .encode('utf-8')

    def push(self, **kwargs):
        new_env = Environment(_parent=self, **kwargs)
        self._children.append(weakref.ref(new_env))
        return new_env

    def keys(self):
        result = self._data.keys()
        if self._parent is not None:
            result += self._parent.keys()
        result = list(set(result))
        result.sort()
        return result

    def is_parent_for(self, env):
        if env._parent is None:
            return False
        elif env._parent == self:
            return True
        else:
            return self.is_parent_for(env._parent)

    def find_parent_of_type(self, type_):
        if self._parent:
            if self._parent.type == type_:
                return self._parent
            return self._parent.find_parent_of_type(type_)

    def get_parent(self):
        return self._parent

    def get_children(self):
        return filter(None,
                      (ref() for ref in self._children))



def _serialize_date(value):
    if value:
        return '{0:%Y-%m-%d}'.format(value)


def _deserialize_date(value):
    if value:
        return arrow.get(value).date()


def _serialize_field(key, value):
    if key in ('date',):
        return _serialize_date(value)
    return value


def _deserialize_field(key, value):
    if key in ('date',):
        return _deserialize_date(value)
    return value


def _serialize(env):
    return {
        key: _serialize_field(key, getattr(env, key))
        for key in env.keys()
    }


def _deserialize(env):
    attrs = {
        key: _deserialize_field(key, value)
        for key, value in env.items()
    }
    return Environment(**attrs)


def serialize_envs(envs):
    """Serialize envs to string as a json.
    Returns text.
    """
    prepared = map(_serialize, envs)

    return anyjson.dumps(prepared)


def deserialize_envs(text):
    """Reads json from given text and transforms some fields.
    """
    envs = anyjson.deserialize(text)
    return map(_deserialize, envs)
