#!/usr/bin/env python
#
# Copyright 2010 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#

"""Client module.  Contains classes to handle authentication and
authorization for Munki clients acting against Simian server.

Classes:

  AuthSessionSimianClient:  Session storage for Simian clients
  AuthSimianClient:         Simian client Auth class
"""




from simian.auth import base
from simian.auth import util


class Error(Exception):
  """Base"""


class CaParametersError(Error):
  """Error obtaining CA parameters."""


class AuthSessionSimianClient(base.Auth1ClientSession):
  """AuthSession data container used for Simian Auth client."""


class AuthSimianClient(base.Auth1Client):
  """Auth1 client which uses AuthSessionSimianClient for session storage."""

  def __init__(self):
    super(AuthSimianClient, self).__init__()

  def LoadCaParameters(self, settings):
    """Load ca/cert parameters for default CA.

    Args:
      settings: object with attribute level access to settings.
    Raises:
      CaParametersError: if any errors occur loading keys/certs.
    """
    try:
      ca_params = util.GetCaParameters(settings, omit_server_private_key=True)
    except util.CaParametersError, e:
      raise CaParametersError(*e.args)
    self._ca_pem = ca_params.ca_public_cert_pem
    self._server_cert_pem = ca_params.server_public_cert_pem
    self._required_issuer = ca_params.required_issuer

  def GetSessionClass(self):
    return AuthSessionSimianClient
