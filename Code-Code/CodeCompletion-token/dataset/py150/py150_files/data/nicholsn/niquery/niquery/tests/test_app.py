__author__ = 'Nolan Nichols <orcid.org/0000-0003-1099-3328>'

import unittest

from mock import patch

from niquery.app import app, make_celery


class MakeCeleryTestCase(unittest.TestCase):

    @patch('niquery.app.Celery')
    def test_make_celery(self, mock_Celery):
        make_celery(app)
        mock_Celery.assert_called_with(app.import_name,
                                       broker=app.config['CELERY_BROKER_URL'])