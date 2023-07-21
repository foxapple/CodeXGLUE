import datetime
import numpy as np
import pandas as pd
import time

from polaris.ext import PolarisExtension


class TimeSeries(PolarisExtension):
    """Generate a time series dateframe"""

    category = "basic"

    def get(self, slug, cf=None, **kwargs):
        """Handler for getting a DataFrame.

        :param cf: should be in this pattern ``days|2014-05-01|2014-05-29``
        """
        if not cf:
            cf_to = datetime.date.today() - datetime.timedelta(1)
            cf_from = cf_to - datetime.timedelta(30)
        else:
            _, cf_from, cf_to = cf.split('|')
            cf_to = datetime.datetime.strptime(cf_to, "%Y-%m-%d").date() - \
                datetime.timedelta(1)

        func = getattr(self, "get_{}".format(slug))
        return func(cf_from=cf_from, cf_to=cf_to, **kwargs)

    def get_series(self, cf_from, cf_to, cols=1):
        # time.sleep(np.random.randint(1, 10))
        date_range = pd.date_range(cf_from, cf_to)
        df = pd.DataFrame(
            np.random.randint(1, 100, size=(len(date_range), cols)),
            index=date_range
        )
        return df

    def get_series_crossfilter(self, days, **kwargs):
        cf_to = datetime.date.today()
        cf_from = cf_to - datetime.timedelta(int(days))
        return self.get_series(cf_from, cf_to)
