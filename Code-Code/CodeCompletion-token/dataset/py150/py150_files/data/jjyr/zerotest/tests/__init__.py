import logging

from zerotest.common import DEBUG

if not DEBUG:
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    logging.getLogger("zerotest.record.http_recorder").setLevel(logging.ERROR)
