import unittest
import json
import sys
import os
import requests

PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(os.path.join(os.path.join(PATH, '..'), '..'), 'lib'))
import opsmgr

class VerifyApp3(unittest.TestCase):

	def setUp(self):
		self.cfinfo = opsmgr.get_cfinfo()
		self.hostname = 'app3.' + self.cfinfo['apps_domain']
		self.url = 'http://' + self.hostname

	def test_responds_to_hello(self):
		headers = { 'Accept': 'application/json' }
		response = requests.get(self.url + '/hello', headers=headers)
		response.raise_for_status()

	def test_receives_custom_properties(self):
		headers = { 'Accept': 'application/json' }
		response = requests.get(self.url + '/env', headers=headers)
		response.raise_for_status()
		env = response.json()
		self.assertEqual(env.get('AUTHOR'), 'Tile Ninja')
		self.assertEqual(env.get('CUSTOMER_NAME'), "Jimmy's Johnnys")
		self.assertEqual(env.get('STREET_ADDRESS'), 'Cartaway Alley')
		self.assertEqual(env.get('CITY'), 'New Jersey')
		self.assertEqual(env.get('ZIP_CODE'), '90310')
		self.assertEqual(env.get('COUNTRY'), 'US')

	def test_receives_expected_services(self):
		headers = { 'Accept': 'application/json' }
		response = requests.get(self.url + '/env', headers=headers)
		response.raise_for_status()
		env = response.json()
		vcap_services = json.loads(env.get('VCAP_SERVICES'))
		broker1_service = vcap_services.get('service-broker1-service', None)
		self.assertTrue(broker1_service is not None)
		self.assertEquals(len(broker1_service), 1)
		self.assertEquals(broker1_service[0].get('plan'), 'second-plan')
	
	def test_has_versioned_name(self):
		headers = { 'Accept': 'application/json' }
		response = requests.get(self.url + '/env', headers=headers)
		response.raise_for_status()
		env = response.json()
		vcap_application = json.loads(env.get('VCAP_APPLICATION'))
		name = vcap_application.get('application_name')
		self.assertTrue(name.startswith('app3-'))

	def test_is_in_correct_space(self):
		headers = { 'Accept': 'application/json' }
		response = requests.get(self.url + '/env', headers=headers)
		response.raise_for_status()
		env = response.json()
		vcap_application = json.loads(env.get('VCAP_APPLICATION'))
		space= vcap_application.get('space_name')
		self.assertEquals(space, 'test-tile-space')

	def test_does_not_receive_admin_credentials(self):
		headers = { 'Accept': 'application/json' }
		response = requests.get(self.url + '/env', headers=headers)
		response.raise_for_status()
		env = response.json()
		user = env.get('CF_ADMIN_USER')
		username = env.get('CF_ADMIN_USERNAME')
		password = env.get('CF_ADMIN_PASSWORD')
		self.assertTrue(user is None)
		self.assertTrue(username is None)
		self.assertTrue(password is None)

if __name__ == '__main__':
	unittest.main()
