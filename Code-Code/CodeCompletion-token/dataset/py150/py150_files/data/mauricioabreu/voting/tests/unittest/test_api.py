import datetime

import json

import falcon
from falcon import testing

import mock

from sqlalchemy.orm.exc import NoResultFound

from backend import action
from backend.api import api
from backend.models import Voting


class TestVoting(testing.TestBase):
    def before(self):
        self.api = api

    @mock.patch.object(action, 'get_voting')
    def test_get_voting_response_should_return_ok_status(self, mock_voting):
        mock_voting.return_value = Voting(description='Mock description')
        mock_voting.return_value.id = 1
        mock_voting.return_value.created_at = datetime.datetime(2015, 01, 01)
        self.simulate_request('/voting/1')
        assert self.srmock.status == falcon.HTTP_200

    @mock.patch.object(action, 'get_voting')
    def test_get_voting_response_body(self, mock_voting):
        mock_voting.return_value = Voting(description='Mock description')
        mock_voting.return_value.id = 1
        mock_voting.return_value.created_at = datetime.datetime(2015, 01, 01)
        body = self.simulate_request('/voting/1')
        expected_body = [
            '{"id": 1, "description": "Mock description", "created_at": "2015-01-01T00:00:00+00:00", "options": []}'
        ]
        assert body == expected_body

    @mock.patch.object(action, 'get_voting')
    def test_get_voting_when_no_resource_found(self, mock_voting):
        mock_voting.side_effect = NoResultFound
        self.simulate_request('/voting/1')
        assert self.srmock.status == falcon.HTTP_404

    @mock.patch.object(action, 'create_voting')
    def test_post_voting_response_status(self, mock_voting):
        self.simulate_request(
            '/voting',
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps(
                {'description': 'Mock description',
                 'options': [{'description': 'Mock description 1'}, {'description': 'Mock description 2'}]}
            ),
        )
        assert self.srmock.status == falcon.HTTP_200

    @mock.patch.object(action, 'create_voting')
    def test_post_voting_response_location(self, mock_voting):
        mock_voting.return_value = Voting(description='Mock description')
        mock_voting.return_value.id = 1
        mock_voting.return_value.created_at = datetime.datetime(2015, 01, 01)
        self.simulate_request(
            '/voting',
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps(
                {'description': 'Mock description',
                 'options': [{'description': 'Mock description 1'}, {'description': 'Mock description 2'}]}
            ),
        )
        location = self.srmock.headers_dict['location']
        assert location == '/voting/1'

    @mock.patch.object(action, 'create_voting')
    def test_post_server_error_when_exception_is_raised(self, mock_voting):
        mock_voting.side_effect = Exception
        self.simulate_request(
            '/voting',
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps(
                {'description': 'Mock description',
                 'options': [{'description': 'Mock description 1'}, {'description': 'Mock description 2'}]}
            ),
        )
        assert self.srmock.status == falcon.HTTP_500

    @mock.patch.object(action, 'delete_voting')
    def test_delete_existing_voting_should_return_ok_status(self, mock_voting):
        mock_voting.return_value = True
        self.simulate_request(
            '/voting/1',
            method='DELETE'
        )
        assert self.srmock.status == falcon.HTTP_204

    @mock.patch.object(action, 'get_voting_result')
    def test_get_voting_result(self, mock_voting):
        mock_voting.return_value = [
            [{'option': 1, 'total_votes': 10}],
            [{'option': 2, 'total_votes': 20}]
        ]
        body = self.simulate_request(
            '/voting/1/result',
            method='GET',
            headers={'Content-Type': 'application/json'},
            decode='utf-8'
        )
        expected_body = '[[{"option": 1, "total_votes": 10}], [{"option": 2, "total_votes": 20}]]'
        assert self.srmock.status == falcon.HTTP_200
        assert body == expected_body


class TestVote(testing.TestBase):
    def before(self):
        self.api = api

    @mock.patch.object(action, 'vote_for_option')
    def test_vote_for_option(self, mock_action):
        self.simulate_request(
            '/vote',
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps(
                {'option': 1}
            ),
        )
        assert self.srmock.status == falcon.HTTP_204

    @mock.patch.object(action, 'vote_for_option')
    def test_vote_for_option_should_call_action(self, mock_action):
        self.simulate_request(
            '/vote',
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps(
                {'option': 1}
            ),
        )
        assert mock_action.call_args[1]['option_id'] == 1
