# Copyright 2013 Locaweb.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
# @author: Francisco Freire, Locaweb.
# @author: Thiago Morello (morellon), Locaweb.
# @author: Willian Molinari (PotHix), Locaweb.
# @author: Juliano Martinez (ncode), Locaweb.

import os
import socket
import ConfigParser


"""
Configuration file load when bootstraping
"""
config = ConfigParser.ConfigParser()

if ("SIMPLESTACK_CFG" in os.environ):
    config_file = os.environ["SIMPLESTACK_CFG"]
else:
    config_file = "/etc/simplestack/simplestack.cfg"

if os.path.isfile(config_file):
    config.read(config_file)
