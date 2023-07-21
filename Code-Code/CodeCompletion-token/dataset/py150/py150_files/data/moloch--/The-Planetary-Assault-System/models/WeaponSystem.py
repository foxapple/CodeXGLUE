# -*- coding: utf-8 -*-
'''
Created on Mar 12, 2012

@author: moloch

    Copyright [2012]

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
'''


import rpyc
import logging

from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import synonym, relationship
from sqlalchemy.types import Unicode, Boolean, Integer
from models import dbsession, algorithm_association_table, \
    plugin_association_table
from models.BaseObject import BaseObject
from models.Algorithm import Algorithm
from rpyc.utils.ssh import SshContext
from tempfile import NamedTemporaryFile


class WeaponSystem(BaseObject):
    '''
    Holds configuration information for remote agents
    '''

    name = Column(Unicode(16), unique=True, nullable=False)
    initialized = Column(Boolean, default=False, nullable=False)
    ssh_user = Column(Unicode(64), nullable=False)
    ssh_key = Column(Unicode(4096), nullable=False)
    ip_address = Column(Unicode(64), unique=True, nullable=False)
    ssh_port = Column(Integer, default=22, nullable=False)
    service_port = Column(Integer, default=31337, nullable=False)
    cpu_count = Column(Integer, default=1)
    gpu_count = Column(Integer, default=0)
    algorithms = relationship("Algorithm",
        secondary=algorithm_association_table, 
        backref="WeaponSystem"
    )
    plugins = relationship("PluginDetails",
        secondary=plugin_association_table, 
        backref="WeaponSystem"
    )

    @classmethod
    def by_id(cls, weapon_id):
        ''' Return the WeaponSystem object whose id is 'weapon_id' '''
        return dbsession.query(cls).filter_by(id=weapon_id).first()

    @classmethod
    def by_uuid(cls, weapon_uuid):
        ''' Return the WeaponSystem object whose uuid is 'weapon_uuid' '''
        return dbsession.query(cls).filter_by(uuid=unicode(weapon_uuid)).first()

    @classmethod
    def get_all(cls):
        ''' Get all WeaponSystem objects that have been initialized '''
        return dbsession.query(cls).all()

    @classmethod
    def get_uninitialized(cls):
        ''' Get all WeaponSystem objects that have not been initialized '''
        return dbsession.query(cls).filter_by(initialized=False).all()

    @classmethod
    def by_name(cls, weapon_name):
        ''' Return the WeaponSystem object whose name is 'weapon_name' '''
        return dbsession.query(cls).filter_by(name=unicode(weapon_name)).first()

    @classmethod
    def by_ip_address(cls, weapon_ip_address):
        ''' Return the WeaponSystem object whose ip_address is 'weapon_ip_address' '''
        return dbsession.query(cls).filter_by(
            ip_address=unicode(weapon_ip_address)
        ).first()

    @classmethod
    def all_idle(cls):
        ''' Returns a list of systems that are initialized, online and not busy '''
        online_systems = filter(
            lambda weapon_system: weapon_system.is_online(), cls.get_all()
        )
        return filter(
            lambda weapon_system: not weapon_system.is_busy(), online_systems
        )

    @classmethod
    def system_ready(cls, algo):
        ''' Returns list of ready systems based on algo '''
        return filter(
            lambda weapon_system: algo in weapon_system.algorithms, cls.all_idle()
        )

    def get_rpc_connection(self, *args):
        ''' initialization, gathers system information '''
        logging.info("Preforming weapon system initialization")
        return self.__connect__()

    def is_online(self):
        ''' Checks if a system is online '''
        rpc_connection = self.__connect__()
        if rpc_connection is not None:
            return rpc_connection.root.exposed_ping() == "PONG"
        else:
            return False

    def is_busy(self):
        ''' Checks to see if a remote system is busy returns bool, or none '''
        rpc_connection = self.__connect__()
        if rpc_connection is not None:
            return rpc_connection.root.exposed_is_busy()

    def __connect__(self):
        '''
        Creates an ssh connection and returns the rpc_connection object
        The ssh keyfile is destroyed when the object is garbage collected.
        '''
        try:
            self.ssh_keyfile = NamedTemporaryFile()
            self.ssh_keyfile.write(self.ssh_key)
            self.ssh_keyfile.seek(0)
            ssh_context = SshContext(self.ip_address,
                user=self.ssh_user, 
                keyfile=self.ssh_keyfile.name
            )
            return rpyc.ssh_connect(ssh_context, self.service_port)
        except:
            logging.exception("Connection to remote weapon system failed")

    def __plugin__(self, rpc_connection):
        categories = rpc_connection.root.exposed_get_categories()
        for category in categories:
            logging.debug("Query weapon system for plugin category: %s" % category)
            plugins = rpc_connection.root.exposed_get_category_plugins(category)
            logging.debug("Found %d plugin(s) loaded by remote agent" % len(plugins))
            for plugin_name in plugins:
                logging.debug("Query details for plugin '%s'" % plugin_name)
                details = rpc_connection.root.exposed_get_plugin_details(plugin_name)
                plugin_info = PluginDetails(**details)
                dbsession.add(plugin_info)
                self.plugins.append(plugin_info)

    def __repr__(self):
        return "<(WeaponSystem) Name: %s, SSh User: %s, LPort: %d, SrvPort: %d>" % (
            self.name, self.ssh_user, self.ssh_port, self.service_port
        )