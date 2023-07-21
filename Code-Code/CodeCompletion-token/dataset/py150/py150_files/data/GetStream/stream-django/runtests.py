import os
import sys


os.environ['DJANGO_SETTINGS_MODULE'] = 'test_app.settings'
test_dir = os.path.join(os.path.dirname(__file__), 'stream_django', 'tests')
sys.path.insert(0, test_dir)

from django.test.utils import get_runner
from django.conf import settings


def runtests():
    import django
    # django 1.6 breaks
    if hasattr(django, 'setup'):
        django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=1, interactive=True)
    failures = test_runner.run_tests(['test_app'])
    sys.exit(bool(failures))


if __name__ == '__main__':
    runtests()
