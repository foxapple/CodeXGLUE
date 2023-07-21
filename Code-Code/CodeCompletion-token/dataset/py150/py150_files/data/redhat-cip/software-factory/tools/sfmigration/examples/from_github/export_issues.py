#!/bin/env python
#
# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os.path

from sfmigration.common.softwarefactory import SFRedmineMigrator
from sfmigration.common import utils
from sfmigration.issues.github import GithubImporter


logger = utils.logger


def get_values(config_file='config.ini'):
    # check config file is present or not
    if not os.path.isfile(config_file):
        logger.error("config file is missing")
        raise
    source_github = {'username': '',
                     'password': '',
                     'repo_owner': '',
                     'repository': ''}
    for key in source_github.iterkeys():
        source_github[key] = utils.get_config_value(config_file,
                                                    'GITHUB', key)
    dest_redmine = {'username': '', 'password': '',
                    'id': '', 'url': '', 'name': '',
                    'sf_domain': '', 'versions_to_skip': [],
                    'issues_to_skip': []}
    for key in dest_redmine.iterkeys():
        dest_redmine[key] = utils.get_config_value(config_file,
                                                   'DEST_REDMINE', key)
    # if url ends with backslash, remove it before use.
    if dest_redmine['url'].endswith('/'):
        dest_redmine['url'] = dest_redmine['url'][:-1]
    versions_to_skip = utils.get_config_value(config_file,
                                              'SKIP', 'version_id')
    if versions_to_skip:
        dest_redmine['versions_to_skip'] = versions_to_skip.split(',')
    issues_to_skip = utils.get_config_value(config_file,
                                            'SKIP', 'issue_id')
    if issues_to_skip:
        dest_redmine['issues_to_skip'] = issues_to_skip.split(',')
    dest_redmine['mapper'] = utils.ConfigMapper('config.ini')
    return source_github, dest_redmine


def main(config_file='config.ini'):
    source_github, dest_redmine = get_values()
    source = GithubImporter(**source_github)
    target = SFRedmineMigrator(**dest_redmine)
    target.migrate(source)

if __name__ == "__main__":
    main()
