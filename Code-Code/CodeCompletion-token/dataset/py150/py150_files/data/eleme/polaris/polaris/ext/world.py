"""
    polaris.ext.world
    ~~~~~~~~~~~~~~~~~

    :copyright: (c) 2013 Eleme, http://polaris.eleme.io
    :license: MIT

    The world extension will return country geojson based on name.
    This extension is mainly for example demo.
"""

import json
from urllib.request import urlopen

from polaris.ext import PolarisCacheExtension


class World(PolarisCacheExtension):
    """Return country geojson based on name.
    """

    category = "map"

    def __init__(self, **kwargs):
        super(World, self).__init__(**kwargs)
        self.url_tpl = ("http://rawgithub.com/johan/world.geo.json/"
                        "master/countries/{}.geo.json")

    def get(self, name="CHN", **kwargs):
        """Request johan/world.geo.json to get geojson and return it as result.
        """
        url = self.url_tpl.format(name)
        req = urlopen(url)
        if not req.status == 200:
            return {}

        _json = json.loads(req.read().decode('utf-8'))

        # here we'll add the source link as geojson info.
        # this is a demo of how to embed additional info into geojson
        for feature in _json["features"]:
            atag = "<a href='{0}'>{1}.geo.json</a>".format(url, name)
            feature["properties"]["source"] = atag

        return {"geojson": _json}
