# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
import logging
import _mysql as mysqldb
import _mysql_exceptions
from contextlib import contextmanager
from . import BaseDriver
from . import DatabaseInfraStatus
from . import AuthenticationError
from . import ConnectionError
from . import GenericDriverError
from . import DatabaseAlreadyExists
from . import InvalidCredential
from . import DatabaseStatus
from . import DatabaseDoesNotExist
from . import CredentialAlreadyExists
from util import make_db_random_password
from system.models import Configuration
from workflow.settings import DEPLOY_MYSQL
from workflow.settings import RESIZE_MYSQL
from workflow.settings import CLONE_MYSQL
from util import exec_remote_command
from util import build_context_script
from dbaas_cloudstack.models import HostAttr

LOG = logging.getLogger(__name__)

ER_DB_CREATE_EXISTS = 1007
ER_DB_DROP_EXISTS = 1008
ER_ACCESS_DENIED_ERROR = 1045
ER_CANNOT_USER = 1396
ER_WRONG_STRING_LENGTH = 1470
ER_CAN_NOT_CONNECT = 2003
LOST_CONNECTION = 2013

CLONE_DATABASE_SCRIPT_NAME = "mysql_clone.sh"
MYSQL_CONNECTION_DEFAULT_TIMEOUT = 5


class MySQL(BaseDriver):

    default_port = 3306
    RESERVED_DATABASES_NAME = ['admin', 'test', 'mysql', 'information_schema']
    DEPLOY = DEPLOY_MYSQL
    CLONE = CLONE_MYSQL
    RESIZE = RESIZE_MYSQL

    def get_connection(self, database=None):
        # my_instance = self.databaseinfra.instances.all()[0]
        uri = "mysql://<user>:<password>@%s" % (self.databaseinfra.endpoint)
        if database:
            uri = "%s/%s" % (uri, database.name)
        return uri

    def get_connection_dns(self, database=None):
        # my_instance = self.databaseinfra.instances.all()[0]
        uri = "mysql://<user>:<password>@%s" % (
            self.databaseinfra.endpoint_dns)
        if database:
            uri = "%s/%s" % (uri, database.name)
        return uri

    def __get_admin_connection(self, instance=None):
        """
        endpoint is on the form HOST:PORT
        """
        if instance:
            return instance.address, instance.port

        endpoint = self.databaseinfra.endpoint.split(':')
        return endpoint[0], int(endpoint[1])

    def __mysql_client__(self, instance, database='mysql'):
        connection_address, connection_port = self.__get_admin_connection(
            instance)
        try:
            LOG.debug(
                'Connecting to mysql databaseinfra %s', self.databaseinfra)
            # mysql uses timeout in seconds
            connection_timeout_in_seconds = Configuration.get_by_name_as_int(
                'mysql_connect_timeout', default=MYSQL_CONNECTION_DEFAULT_TIMEOUT)

            client = mysqldb.connect(host=connection_address, port=int(connection_port),
                                     user=self.databaseinfra.user, passwd=self.databaseinfra.password,
                                     db=database, connect_timeout=connection_timeout_in_seconds)
            LOG.debug(
                'Successfully connected to mysql databaseinfra %s' % (self.databaseinfra))
            return client
        except Exception as e:
            raise e

    def get_client(self, instance):
        return self.__mysql_client__(instance)

    def lock_database(self, client):
        client.query("SET session lock_wait_timeout = 60")
        client.query("flush tables with read lock")
        client.query("flush logs")

    def unlock_database(self, client):
        client.query("unlock tables")

    @contextmanager
    def mysqldb(self, instance=None, database=None):
        client = None
        try:
            yield self.__mysql_client__(instance)
        except _mysql_exceptions.OperationalError as e:
            if e.args[0] == ER_ACCESS_DENIED_ERROR:
                raise AuthenticationError(e.args[1])
            elif e.args[0] == ER_CAN_NOT_CONNECT:
                raise ConnectionError(e.args[1])
            elif e.args[0] == LOST_CONNECTION:
                raise ConnectionError(e.args[1])
            else:
                raise GenericDriverError(e.args)
        finally:
            try:
                if client:
                    LOG.debug(
                        'Disconnecting mysql databaseinfra %s', self.databaseinfra)
                    client.close()
            except:
                LOG.warn('Error disconnecting from databaseinfra %s. Ignoring...',
                         self.databaseinfra, exc_info=True)

    def __query(self, query_string, instance=None):
        with self.mysqldb(instance=instance) as client:
            try:
                LOG.debug("query_string: %s" % query_string)
                client.query(query_string)
                r = client.store_result()
                if r is not None:
                    return r.fetch_row(maxrows=0, how=1)
            except _mysql_exceptions.ProgrammingError as e:
                LOG.error("__query ProgrammingError: %s" % e)
                if e.args[0] == ER_DB_CREATE_EXISTS:
                    raise DatabaseAlreadyExists(e.args[1])
                else:
                    raise GenericDriverError(e.args)
            except _mysql_exceptions.OperationalError as e:
                LOG.error("__query OperationalError: %s" % e)
                if e.args[0] == ER_DB_DROP_EXISTS:
                    raise DatabaseDoesNotExist(e.args[1])
                elif e.args[0] == ER_CANNOT_USER:
                    raise InvalidCredential(e.args[1])
                elif e.args[0] == ER_WRONG_STRING_LENGTH:
                    raise InvalidCredential(e.args[1])
                else:
                    raise GenericDriverError(e.args)
            except Exception as e:
                GenericDriverError(e.args)

    def info(self):
        from logical.models import Database

        databaseinfra_status = DatabaseInfraStatus(
            databaseinfra_model=self.databaseinfra)

        r = self.__query("SELECT VERSION()")
        databaseinfra_status.version = r[0]['VERSION()']

        my_all_dbs = self.__query("SHOW DATABASES")
        db_sizes = self.__query("SELECT s.schema_name 'Database', ifnull(SUM( t.data_length + t.index_length), 0) 'Size' \
                                FROM information_schema.SCHEMATA s \
                                  left outer join information_schema.TABLES t on s.schema_name = t.table_schema \
                                GROUP BY s.schema_name")

        all_dbs = {}
        for database in db_sizes:
            all_dbs[database['Database']] = int(database['Size'])

        list_databases = self.list_databases()
        for database_name in all_dbs.keys():
            database_model = None
            try:
                # LOG.debug("checking status for database %s" % database_name)
                database_model = Database.objects.get(
                    name=database_name, databaseinfra=self.databaseinfra)
            except Database.DoesNotExist:
                pass

            if database_model:
                db_status = DatabaseStatus(database_model)
                # is_alive?
                try:
                    if self.check_status() and (database_name in list_databases):
                        db_status.is_alive = True
                except Exception as e:
                    LOG.warning(
                        "could not retrieve db status for %s: %s" % (database_name, e))

                db_status.total_size_in_bytes = 0
                db_status.used_size_in_bytes = all_dbs[database_name]

                databaseinfra_status.databases_status[
                    database_name] = db_status

        databaseinfra_status.used_size_in_bytes = sum(all_dbs.values())

        return databaseinfra_status

    def check_status(self, instance=None):
        status = False
        try:
            result = self.__query("SELECT 1", instance=instance)
            if result[0]['1'] == '1':
                status = True
        except Exception as e:
            LOG.warning(
                "could not retrieve status for instance %s: %s" % (instance, e))

        return status

    def create_database(self, database):
        LOG.info("creating database %s" % database.name)
        self.__query("CREATE DATABASE %s" % database.name)

    def create_user(self, credential, roles=["ALL PRIVILEGES"]):
        LOG.info("creating user %s to %s" %
                 (credential.user, credential.database))
        # the first release allow every host to connect to the database
        # 2 steps required to get the user create error
        if credential.user in self.list_users():
            raise CredentialAlreadyExists()
        self.__query("CREATE USER '%s'@'%%' IDENTIFIED BY '%s'" %
                     (credential.user, credential.password))
        self.__query("GRANT %s ON %s.* TO '%s'@'%%'" %
                     (','.join(roles), credential.database, credential.user))

    def remove_database(self, database):
        LOG.info("removing database %s" % (database.name))
        self.__query("DROP DATABASE %s" % database.name)

    def list_databases(self, instance=None):
        """list databases in a databaseinfra"""
        LOG.info("listing databases in %s" % (self.databaseinfra))
        results = self.__query("SHOW databases", instance=instance)
        return [result["Database"] for result in results]

    def disconnect_user(self, credential):
        # It works only in mysql >= 5.5
        r = self.__query("SELECT id FROM information_schema.processlist WHERE user='%s' AND db='%s'" %
                         (credential.user, credential.database))
        for session in r:
            LOG.info("disconnecting user %s from database %s id_session %s" %
                     (credential.user, credential.database, session['id']))
            self.__query("KILL CONNECTION %s" % session['id'])

    def remove_user(self, credential):
        LOG.info("removing user %s from %s" %
                 (credential.user, credential.database))
        self.disconnect_user(credential)
        self.__query("DROP USER '%s'@'%%'" % credential.user)

    def update_user(self, credential):
        self.remove_user(credential)
        self.create_user(credential)

    def list_users(self, instance=None):
        LOG.info("listing users in %s" % (self.databaseinfra))
        results = self.__query(
            "SELECT distinct User FROM mysql.user where User != ''", instance=instance)
        return [result["User"] for result in results]

    def change_default_pwd(self, instance):
        new_password = make_db_random_password()
        self.__query("SET PASSWORD FOR '%s'@'%%' = PASSWORD('%s')" (
            instance.databaseinfra.user, new_password))
        return new_password

    def clone(self):
        return CLONE_DATABASE_SCRIPT_NAME

    def check_instance_is_eligible_for_backup(self, instance):
        if self.databaseinfra.instances.count() == 1:
            return True
        results = self.__query(
            query_string="show variables like 'read_only'", instance=instance)
        if results[0]["Value"] == "ON":
            return True
        else:
            return False

    def check_instance_is_master(self, instance):
        if self.databaseinfra.instances.count() == 1:
            return True
        results = self.__query(
            query_string="show variables like 'read_only'", instance=instance)
        if results[0]["Value"] == "ON":
            return False
        else:
            return True

    def get_replication_info(self, instance):
        results = self.__query(
            query_string="show slave status", instance=instance)
        seconds_behind_master = results[0]['Seconds_Behind_Master']
        if seconds_behind_master is None:
            raise Exception("Replication is not running")
        return int(seconds_behind_master)

    def is_replication_ok(self, instance):
        if self.get_replication_info(instance=instance) == 0:
            return True

        return False

    def initialization_script_path(self,):
        return "/etc/init.d/mysql"

    def deprecated_files(self,):
        return ['*.pid', "*.err", "auto.cnf"]

    def data_dir(self, ):
        return '/data/data/'

    def switch_master(self):
        master = self.get_master_instance()
        slave = self.get_slave_instances()[0]
        host = master.hostname

        host_attr = HostAttr.objects.get(host=host)

        script = """
        sudo -u flipper /usr/bin/flipper {{MASTERPAIRNAME}} set write {{HOST01.address}}
        sudo -u flipper /usr/bin/flipper {{MASTERPAIRNAME}} set read {{HOST02.address}}
        """

        context_dict = {
            'MASTERPAIRNAME': self.databaseinfra.name,
            'HOST01': slave.hostname,
            'HOST02': master.hostname,
        }
        script = build_context_script(context_dict, script)
        output = {}
        return_code = exec_remote_command(server=host.address,
                                          username=host_attr.vm_user,
                                          password=host_attr.vm_password,
                                          command=script,
                                          output=output)
        LOG.info(output)
        if return_code != 0:
            raise Exception(str(output))

    def start_slave(self, instance):
        client = self.get_client(instance)
        client.query("start slave")

    def get_database_agents(self):
        common = ['td-agent', 'mysql_statsd', 'monit']
        if self.databaseinfra.plan.is_ha:
            return common + ['httpd', 'mk-heartbeat-daemon']

        return common
