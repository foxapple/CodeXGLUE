import sure
from django.test import TestCase
from tasks.const import STATUS_SUCCESS, STATUS_FAILED
from ..pep8 import pep8_violation
from .base import get_content


class PEP8ViolationCase(TestCase):
    """PEP8 violation case"""

    def test_success(self):
        """Test success result"""
        data = {'raw': ''}
        result = pep8_violation(data)
        result['status'].should.be.equal(STATUS_SUCCESS)
        result['plot']['count'].should.be.equal(0)

    def test_fail_on_real(self):
        """Test fail on real data"""
        data = {
            'raw': get_content('pep8.out'),
        }
        result = pep8_violation(data)
        result['status'].should.be.equal(STATUS_FAILED)
        result['plot']['count'].should.be.equal(307)
