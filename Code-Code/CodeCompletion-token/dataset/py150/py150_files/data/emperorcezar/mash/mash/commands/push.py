import sys
import os
from sys import stderr
import subprocess
import ConfigParser
import yaml
from urlparse import urlparse

from mash import BaseCommand, MashServerException
from mash.commands.config import ConfigMixin
from mash.envs import MashEnvs

from fabric.api import settings, run, sudo
from fabric.operations import get
from fabric.context_managers import prefix, cd
from fabric.contrib.files import exists
from fabric.contrib.project import rsync_project


from os.path import join


class Command(BaseCommand, ConfigMixin):
    @classmethod
    def add_options(cls, parser):
        parser.add_argument('server')

    @classmethod
    def get_defaults(cls):
        # Set the default builpacks
        options = dict()
        
        options['buildpacks'] = [
            'https://github.com/instituteofdesign/buildpack-python.git'
        ]

        options['buildpack_dir'] = False
    
        return options
        
    def go(self):
        '''
        This is where the magic happens
        '''
        setting_args = self.get_setting_args()
        envconfig = False
        
        with settings(**setting_args):
            # Create the directories we need
            self.setup_directories()
            
            # Make sure our buildpacks are in place
            self.setup_buildpacks()

            # Pull down our env config
            if self.config_exists():
                envconfig = self.get_config()
            
            # Rsync our current project up
            rsync_project(self.build_dir, local_dir = "{}/".format(os.getcwd()), exclude = ['.git', '.gitignore'])
            
            # Check our buildpacks
            output = run('ls {}'.format(self.buildpack_dir))
            packs = [f for f in output.split() if f not in ['.', '..']]
            buildpack = False
            for pack in packs:
                with settings(warn_only = True), prefix("cd {}".format(join(self.buildpack_dir, pack))):
                    out = run("bin/detect {}".format(self.build_dir))
                    if out.return_code != 0:
                        continue
                    else:
                        name = out
                        buildpack = pack
                        break

            assert buildpack

            with prefix("cd {}".format(join(self.buildpack_dir, pack))), prefix("export NAME={}".format(name)):
                # Run compile
                run("bin/compile {} {}".format(self.build_dir, self.cache_dir))
                # Run release
                out = run("bin/release {} {}".format(self.build_dir, self.cache_dir))

                if out.return_code != 0:
                    print >> stderr, "Release broke"
                    exit(out.return_code)
            
                
            # We look for a release path from the call then from the release buildpack, then from a .env
            release = yaml.load(out)
            config = release.get('config_vars', False)

            if not envconfig:
                # Write the defaults into the .env
                envconfig = MashEnvs(config = config)

            # Put our .env back
            self.put_config(envconfig)
            
            

