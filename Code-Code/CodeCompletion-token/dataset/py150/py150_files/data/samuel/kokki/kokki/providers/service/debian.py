
__all__ = ["DebianServiceProvider"]

from kokki.providers.service import ServiceProvider

class DebianServiceProvider(ServiceProvider):
    def enable_runlevel(self, runlevel):
        pass
