# Copyright 2014 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit test for GitkitClient."""

import base64
import unittest
try:
    from urllib import parse
    from unittest import mock
except ImportError:
    import urlparse as parse
    import mock

from identitytoolkit import errors
from identitytoolkit import gitkitclient


class GitkitClientTestCase(unittest.TestCase):

  def setUp(self):
    self.widget_url = 'http://localhost:9000/widget'
    self.user_id = '1234'
    self.email = 'user@example.com'
    self.user_name = 'Joe'
    self.user_photo = 'http://idp.com/photo'
    self.gitkitclient = gitkitclient.GitkitClient(client_id='client_id',
                                                  widget_url=self.widget_url)

  def testGetClientId(self):
    expected_client_id = 'client_id'
    with mock.patch('identitytoolkit.rpchelper.RpcHelper.GetProjectConfig') as rpc_mock:
        rpc_mock.return_value = {
            'idpConfig': [{
                'provider': 'GOOGLE',
                'clientId': expected_client_id,
            }]
        }
        actual_client_id = self.gitkitclient.GetClientId()
        self.assertEqual(actual_client_id, expected_client_id)

  def testGetClientId_throwException(self):
    with mock.patch('identitytoolkit.rpchelper.RpcHelper.GetProjectConfig') as rpc_mock:
        rpc_mock.return_value = {
            'idpConfig': []
        }
        try:
          self.gitkitclient.GetClientId()
          self.fail('GitkitServerException expected')
        except errors.GitkitServerError as error:
          self.assertEqual('Google client ID not configured yet.', error.value)

  def testGetBrowserApiKey(self):
    expected_api_key = 'api_key'
    with mock.patch('identitytoolkit.rpchelper.RpcHelper.GetProjectConfig') as rpc_mock:
        rpc_mock.return_value = {
            'apiKey': expected_api_key,
        }
        actual_api_key = self.gitkitclient.GetBrowserApiKey()
        self.assertEqual(actual_api_key, expected_api_key)

  def testGetSignInOptions(self):
    with mock.patch('identitytoolkit.rpchelper.RpcHelper.GetProjectConfig') as rpc_mock:
        rpc_mock.return_value = {
            'allowPasswordUser': True,
            'idpConfig': [{
                'provider': 'GOOGLE',
                'enabled': True,
            }]
        }
        sign_in_options = self.gitkitclient.GetSignInOptions()
        self.assertEqual(sign_in_options, ['google', 'password'])

  def testGetSignInOptions_throwEmpty(self):
    with mock.patch('identitytoolkit.rpchelper.RpcHelper.GetProjectConfig') as rpc_mock:
        rpc_mock.return_value = {
            'allowPasswordUser': False,
            'idpConfig': [{
                'provider': 'GOOGLE',
                'enabled': False,
            }]
        }
        try:
          self.gitkitclient.GetSignInOptions()
          self.fail('GitkitServerException expected')
        except errors.GitkitServerError as error:
          self.assertEqual('no sign in option configured', error.value)

  def testVerifyToken(self):
    with mock.patch('identitytoolkit.rpchelper.RpcHelper.GetPublicCert') as rpc_mock:
      rpc_mock.return_value = {'kid': 'cert'}
      with mock.patch('oauth2client.crypt.'
                      'verify_signed_jwt_with_certs') as crypt_mock:
        crypt_mock.return_value = {
            'localId': self.user_id,
            'email': self.email,
            'display_name': self.user_name
        }
        gitkit_user = self.gitkitclient.VerifyGitkitToken('token')
        self.assertEqual(self.user_id, gitkit_user.user_id)
        self.assertEqual(self.email, gitkit_user.email)
        self.assertEqual(self.user_name, gitkit_user.name)
        self.assertIsNone(gitkit_user.photo_url)
        self.assertEqual({}, gitkit_user.provider_info)

  def testGetAccountInfo(self):
    with mock.patch('identitytoolkit.rpchelper.RpcHelper._InvokeGitkitApi') as rpc_mock:
      rpc_mock.return_value = {'users': [{
          'email': self.email,
          'localId': self.user_id,
          'displayName': self.user_name,
          'photoUrl': self.user_photo
      }]}
      gitkit_user = self.gitkitclient.GetUserByEmail(self.email)
      self.assertEqual(self.user_id, gitkit_user.user_id)
      self.assertEqual(self.email, gitkit_user.email)
      self.assertEqual(self.user_name, gitkit_user.name)
      self.assertEqual(self.user_photo, gitkit_user.photo_url)

  def testUploadAccount(self):
    hash_algorithm = gitkitclient.ALGORITHM_HMAC_SHA256
    try:
        hash_key = bytes('key123', 'utf-8')
    except TypeError:
        hash_key = 'key123'
    upload_user = gitkitclient.GitkitUser.FromDictionary({
        'email': self.email,
        'localId': self.user_id,
        'displayName': self.user_name,
        'photoUrl': self.user_photo
    })
    with mock.patch('identitytoolkit.rpchelper.RpcHelper._InvokeGitkitApi') as rpc_mock:
      rpc_mock.return_value = {}
      self.gitkitclient.UploadUsers(hash_algorithm, hash_key, [upload_user])
      expected_param = {
          'hashAlgorithm': hash_algorithm,
          'signerKey': base64.urlsafe_b64encode(hash_key),
          'users': [{
              'email': self.email,
              'localId': self.user_id,
              'displayName': self.user_name,
              'photoUrl': self.user_photo
          }]
      }
      rpc_mock.assert_called_with('uploadAccount', expected_param)

  def testDownloadAccount(self):
    with mock.patch('identitytoolkit.rpchelper.RpcHelper._InvokeGitkitApi') as rpc_mock:
      # First paginated request
      rpc_mock.return_value = {
          'nextPageToken': '100',
          'users': [
              {'email': self.email, 'localId': self.user_id},
              {'email': 'another@example.com', 'localId': 'another'}
          ]
      }
      iterator = self.gitkitclient.GetAllUsers()
      self.assertEqual(self.email, next(iterator).email)
      self.assertEqual('another@example.com', next(iterator).email)

      # Should stop since no more result
      rpc_mock.return_value = {}
      with self.assertRaises(StopIteration):
        next(iterator)

      expected_call = [(('downloadAccount', {'maxResults': 10}),),
                       (('downloadAccount',
                         {'nextPageToken': '100', 'maxResults': 10}),)]
      self.assertEqual(expected_call, rpc_mock.call_args_list)

  def testGetOobResult(self):
    code = '1234'
    with mock.patch('identitytoolkit.rpchelper.RpcHelper._InvokeGitkitApi') as rpc_mock:
      rpc_mock.return_value = {'oobCode': code}
      widget_request = {
          'action': 'resetPassword',
          'email': self.email,
          'response': '8888'
      }
      result = self.gitkitclient.GetOobResult(widget_request, '1.1.1.1')
      self.assertEqual('resetPassword', result['action'])
      self.assertEqual(self.email, result['email'])
      self.assertEqual(code, result['oob_code'])
      self.assertEqual('{"success": true}', result['response_body'])
      self.assertTrue(result['oob_link'].startswith(self.widget_url))
      url = parse.urlparse(result['oob_link'])
      query = parse.parse_qs(url.query)
      self.assertEqual('resetPassword', query['mode'][0])
      self.assertEqual(code, query['oobCode'][0])

  def testGetEmailVerificationLink(self):
      code = '1234'
      with mock.patch('identitytoolkit.rpchelper.RpcHelper._InvokeGitkitApi') as rpc_mock:
          rpc_mock.return_value = {'oobCode': code}
          result = self.gitkitclient.GetEmailVerificationLink('user@example.com')
          self.assertTrue(result.startswith(self.widget_url))
          url = parse.urlparse(result)
          query = parse.parse_qs(url.query)
          self.assertEqual('verifyEmail', query['mode'][0])
          self.assertEqual(code, query['oobCode'][0])
      

if __name__ == '__main__':
  unittest.main()
