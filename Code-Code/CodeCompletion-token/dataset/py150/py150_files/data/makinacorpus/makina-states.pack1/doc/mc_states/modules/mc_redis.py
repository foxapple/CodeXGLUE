# -*- coding: utf-8 -*-
'''
.. _module_mc_redis:

mc_redis / redis functions
============================================



'''

# Import python libs
import logging
import mc_states.api
from salt.utils.odict import OrderedDict as _OrderedDict

__name = 'redis'

log = logging.getLogger(__name__)


def settings():
    '''
    redis settings

    location
        installation directory

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        redis_reg = __salt__[
            'mc_macros.get_local_registry'](
                'redis', registry_format='pack')
        pw = redis_reg.setdefault(
            'password', __salt__['mc_utils.generate_password']())
        locs = __salt__['mc_locations.settings']()
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.db.redis', {
                'admin': 'admin',
                'password': pw,
                'templates': _OrderedDict([
                    ('/etc/default/redis-server', {}),
                    ('/etc/redis/redis.conf', {})]),
                'packages':  [
                    'redis-server',
                    'libredis-perl',
                    'python-redis',
                    'redis-tools',
                ],
                'service': 'redis-server',
                'ulimit': '65536',
                'redis': {
                    'port': 6379,
                    'masterauth_format': '##{0}',
                    'masterauth': '',
                    'requirepass_format': '{0}',
                    'requirepass': '',
                    'bind': '0.0.0.0',
                    'unixsocket': '/var/run/redis/redis.sock',
                    'unixsocketperm': '755',
                    'timeout': 0,
                    'keepalive': 0,
                    'loglevel': 'notice',
                    'logfile': '/var/log/redis/redis-server.log',
                    'databases': 16,
                    'save': ['900 1',
                             '300 10',
                             '60 10000'],
                    'stop-writes-on-bgsave-error': 'yes',
                    'rdbcompression': 'yes',
                    'rdbchecksum': 'yes',
                    'dbfilename': 'dump.rdb',
                    'dir': '/var/lib/redis',
                    'slave-serve-stale-data': 'yes',
                    'slave-read-only': 'yes',
                    'repl-disable-tcp-nodelay': 'no',
                    'slave-priority': '100',
                    'aof-rewrite-incremental-fsync': 'yes',
                    'appendonly': 'no',
                    'appendfsync': 'everysec',
                    'no-appendfsync-on-rewrite': 'no',
                    'lua-time-limit': 5000,
                    'auto-aof-rewrite-percentage': 100,
                    'hash-max-ziplist-entries': 512,
                    'hash-max-ziplist-value': 64,
                    'activerehashing': 'yes',
                    'list-max-ziplist-entries': 512,
                    'daemonize': 'yes',
                    'pidfile': '/var/run/redis/redis-server.pid',
                    'list-max-ziplist-value': 64,
                    'set-max-intset-entries': 512,
                    'zset-max-ziplist-entries': 128,
                    'zset-max-ziplist-value': 64,
                    'slaveof': '##<masterip> <masterport>',
                    'slowlog-log-slower-than': 10000,
                    'slowlog-max-len': 128,
                    'notify-keyspace-events': '""',
                    'hz': 10,
                    'auto-aof-rewrite-min-size': '64mb',
                    'client-output-buffer-limit': ['normal 0 0 0',
                                                   'slave 256mb 64mb 60',
                                                   'pubsub 32mb 8mb 60'],
                }
            })
        for i in ['requirepass', 'masterauth']:
            data['redis'][i] = data['redis'][i + '_format'].format(pw)
        __salt__['mc_macros.update_local_registry'](
            'redis', redis_reg,
            registry_format='pack')
        return data
    return _settings()



#
