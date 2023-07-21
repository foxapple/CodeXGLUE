# -*- coding: utf-8 -*-

class NeedOverrideError(NotImplementedError):
    def __init__(self, errmsg='You need override this method'):
        super(NeedOverrideError, self).__init__(self, errmsg)

class ConfigError(Exception):
    pass

class UnsupportDefinitionType(ConfigError):
    pass

class UndefinedFilterException(ConfigError):
    pass