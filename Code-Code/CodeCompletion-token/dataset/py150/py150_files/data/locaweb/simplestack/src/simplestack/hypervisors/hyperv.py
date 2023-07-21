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

from simplestack.hypervisors.base import SimpleStack

import libvirt


class Stack(SimpleStack):

    def __init__(self, hostinfo):
        self.connection = False
        self.hostinfo = hostinfo
        self.connect()

    def libvirt_connect(self):
        open_flags = 0
        valid_auth_options = [
            libvirt.VIR_CRED_AUTHNAME, libvirt.VIR_CRED_NOECHOPROMPT
        ]
        authcb = None
        authcb_data = None

        uri = "hyperv://%s@%s/?transport=http" % (
            self.hostinfo.get("username"), self.hostinfo.get("api_server")
        )
        self.connection = libvirt.openAuth(
            uri, [valid_auth_options, authcb, authcb_data], open_flags
        )

    def connect(self):
        self.libvirt_connection = self.libvirt_connect()
        self.connection = self.libvirt_connection
