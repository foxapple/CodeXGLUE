########
# Copyright (c) 2013 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.


from testenv import TestCase
from testenv.utils import get_resource as resource
from testenv.utils import deploy_application as deploy


class GetInstanceIPTest(TestCase):

    def test_get_instance_ip(self):
        dsl_path = resource("dsl/get_instance_ip.yaml")
        deployment, _ = deploy(dsl_path)

        invocations = self.get_plugin_data(
            plugin_name='testmockoperations',
            deployment_id=deployment.id
        )['mock_operation_invocation']
        mapping = {name: ip for name, ip in invocations}
        self.assertDictEqual({
            'host1_1': '1.1.1.1',
            'host1_2': '2.2.2.2',
            'contained1_in_host1_1': '1.1.1.1',
            'contained1_in_host1_2': '2.2.2.2',
            'host2_1': '3.3.3.3',
            'host2_2': '4.4.4.4',
            'contained2_in_host2_1': '3.3.3.3',
            'contained2_in_host2_2': '4.4.4.4',
            'host2_1_target': '3.3.3.3',
            'host2_2_target': '4.4.4.4',
            'contained2_in_host2_1_source': '3.3.3.3',
            'contained2_in_host2_2_source': '4.4.4.4'
        }, mapping)
