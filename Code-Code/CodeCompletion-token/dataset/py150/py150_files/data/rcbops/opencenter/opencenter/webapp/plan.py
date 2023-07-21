#!/usr/bin/env python
#               OpenCenter(TM) is Copyright 2013 by Rackspace US, Inc.
##############################################################################
#
# OpenCenter is licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.  This
# version of OpenCenter includes Rackspace trademarks and logos, and in
# accordance with Section 6 of the License, the provision of commercial
# support services in conjunction with a version of OpenCenter which includes
# Rackspace trademarks and logos is prohibited.  OpenCenter source code and
# details are available at: # https://github.com/rcbops/opencenter or upon
# written request.
#
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0 and a copy, including this
# notice, is available in the LICENSE file accompanying this software.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the # specific language governing permissions and limitations
# under the License.
#
##############################################################################

import flask

from opencenter.db.api import api_from_models
from opencenter.webapp import generic
# from opencenter.webapp import utility

bp = flask.Blueprint('plan', __name__)


@bp.route('/', methods=['POST'])
def run_plan():
    # this comes in just like an optioned plan.  We'll stuff any returned
    # args and call it a plan.  <rimshot>
    #

    api = api_from_models()

    data = flask.request.json

    if not 'node' in data:
        return generic.http_badrequest(msg='no node specified')

    if not 'plan' in data:
        return generic.http_badrequest(msg='no plan specified')

    plan = data['plan']

    # this is more than a bit awkward
    for step in plan:
        if 'args' in step:
            for arg in step['args']:
                if 'value' in step['args'][arg]:
                    step['ns'][arg] = step['args'][arg]['value']

            step.pop('args')

    # now our plan is a standard plan.  Let's run it
    return generic.http_solver_request(data['node'], [], api=api, plan=plan)
