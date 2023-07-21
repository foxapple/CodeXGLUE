import json
import unittest

from nose.tools import (
    assert_dict_contains_subset,
    assert_equal,
    assert_in,
    assert_true,
)

from _fixtures import PolarisUserFixture


_load_json = lambda rv: json.loads(rv.data.decode(rv.charset))


class PolarisChartTest(PolarisUserFixture):

    basic_chart = {
        "name": "Test Random Chart",
        "slug": "test_random_chart",
        "source": "random",
        "options": {},
        "is_public": True
    }

    def new_basic_chart(self):
        data = json.dumps(self.basic_chart)
        headers = {"X-CSRF-Token": self.csrf}
        rv = self.app.post("/api/charts", data=data,
                           headers=headers, content_type='application/json')
        return _load_json(rv)

    def test_chart_list(self):
        res = _load_json(self.app.get("/api/charts"))
        assert_true(isinstance(res, dict))
        assert_true(isinstance(res["charts"], list))

    def test_chart_new(self):
        chart1 = self.new_basic_chart()["chart"]
        assert_dict_contains_subset(self.basic_chart, chart1)

        # test chart created successful
        rv = self.app.get("/api/chart/{}".format(chart1["id"]))
        assert_equal(rv.status_code, 200)

        chart2 = _load_json(rv)["chart"]
        assert_equal(chart1, chart2)

        # test the new created chart in charts list
        charts = _load_json(self.app.get("/api/charts"))["charts"]
        assert_in(chart1, charts)

    def test_chart_delete(self):
        chart = self.new_basic_chart()["chart"]

        # test delete chart
        headers = {"X-CSRF-Token": self.csrf}
        resource = "/api/chart/{}".format(chart["id"])

        rv = self.app.delete(resource, headers=headers)
        assert_equal(rv.status_code, 200)

        rv = self.app.get(resource)
        assert_equal(rv.status_code, 403)

    def test_chart_edit(self):
        new_chart = {
            "name": "New Random Chart",
            "slug": "new_random_chart",
            "is_public": False,
            "options": {"x": 10}
        }
        chart = self.new_basic_chart()["chart"]
        chart.update(new_chart)

        headers = {"X-CSRF-Token": self.csrf}
        resource = "/api/chart/{}".format(chart["id"])
        rv = self.app.put(resource, data=json.dumps(chart),
                          headers=headers, content_type='application/json')
        assert_equal(rv.status_code, 200)

        new_chart2 = _load_json(rv)["chart"]
        assert_equal(chart, new_chart2)


if __name__ == '__main__':
    unittest.main()
