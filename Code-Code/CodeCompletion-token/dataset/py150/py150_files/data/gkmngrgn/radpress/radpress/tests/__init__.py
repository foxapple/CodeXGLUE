from radpress.compat import has_app

from radpress.tests.base import BaseTest, RestructuredtextTest
from radpress.tests.md import MarkdownTest

if has_app('django.contrib.admin'):
    from radpress.tests.admin import AdminTest
else:
    print("`django.contrib.admin` is not installed, passed admin tests...")
