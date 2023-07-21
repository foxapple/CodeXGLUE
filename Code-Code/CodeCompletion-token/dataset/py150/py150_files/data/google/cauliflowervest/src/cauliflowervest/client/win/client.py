#!/usr/bin/env python
#
# Copyright 2012 Google Inc. All Rights Reserved.
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

"""Module for a client class to manipulate BitLocker keys on CauliflowerVest."""




from cauliflowervest import settings as base_settings
from cauliflowervest.client import base_client


class BitLockerClient(base_client.CauliflowerVestClient):
  """Client to perform BitLocker operations."""

  ESCROW_PATH = '/bitlocker'
  REQUIRED_METADATA = base_settings.BITLOCKER_REQUIRED_PROPERTIES

  def UploadPassphrase(self, volume_uuid, passphrase, metadata):
    self._metadata = metadata
    super(BitLockerClient, self).UploadPassphrase(volume_uuid, passphrase)
