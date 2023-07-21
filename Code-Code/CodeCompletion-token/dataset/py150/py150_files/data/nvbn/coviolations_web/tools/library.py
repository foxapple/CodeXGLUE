from functools import partial


class BaseLibrary(object):
    """Base library"""
    exception = None
    enabled_settings = None

    def __init__(self):
        self._items = {}

    def _register_fnc(self, name, fnc):
        self._items[name] = fnc
        return fnc

    def register(self, name):
        """Register function in library

        :param name: name of method
        :type name: str
        :returns: decorator
        """
        return partial(self._register_fnc, name)

    def get(self, name):
        """Get item from library

        :param name: name of method
        :type name: str
        :returns: method -- registered method
        """
        if self.has(name):
            return self._items[name]
        else:
            raise self.exception(name)

    def has(self, name):
        """Has item in library

        :param name: name of method
        :type name: str
        :returns: bool
        """
        return name in self._items
