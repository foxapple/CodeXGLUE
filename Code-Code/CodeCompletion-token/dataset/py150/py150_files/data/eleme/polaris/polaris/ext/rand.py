"""
    polaris.ext.rand
    ~~~~~~~~~~~~~~~~

    :copyright: (c) 2013 Eleme, http://polaris.eleme.io
    :license: MIT

    The rand extension will generate random series and dataframe based on args.
    This extension is mainly for example demo.
"""

import numpy as np
import pandas as pd

from polaris.ext import PolarisExtension


class Rand(PolarisExtension):
    """Generate random series or dataframe
    """

    category = "basic"

    # global filter
    def gf(self, level="multi"):
        if level == "single":
            return self.single_level_gf()
        else:
            return self.multi_level_gf()

    def single_level_gf(self):
        return [
            {
                "filter": "x",
                "label": "X Chooser",
                "type": "choice",
                "values": [
                    {"name": "reset", "value": None},
                    {"name": 10, "value": 10},
                    {"name": 50, "value": 50},
                    {"name": 100, "value": 100}
                ]
            },
            {
                "filter": "x",
                "label": "X",
                "type": "input",
                "fieldType": "integer"
            },
            {
                "filter": "y",
                "label": "Y",
                "type": "input",
                "fieldType": "integer"
            }
        ]

    def multi_level_gf(self):
        x_values = [{"id": j + 9, "name": str(i), "value": i}
                    for j, i in enumerate(range(3, 100, 2))]
        x_values.insert(0, {"id": 8, "name": "reset", "value": None})

        return [
            {
                "filter": "label",
                "label": "Type",
                "type": "choice",
                "values": [
                    {"id": 0, "name": "reset", "value": None},
                    {
                        "id": 1,
                        "name": "x<40",
                        "value": "x<40",
                        "link": {
                            "sublabel": ["x<10", "10<=x<40"],
                            "x": [str(i) for i in range(3, 40, 2)]
                        }
                    },
                    {
                        "id": 2,
                        "name": "x>=40",
                        "value": "x>=40",
                        "link": {
                            "sublabel": ["40<=x<80", "80<=x<100"],
                            "x": [str(i) for i in range(41, 100, 2)]
                        }
                    }
                ],
                "filteredFor": ["sublabel", "x"]
            },
            {
                "filter": "sublabel",
                "label": "SubType",
                "type": "choice",
                "values": [
                    {"id": 3, "name": "reset", "value": None},
                    {
                        "id": 4,
                        "name": "x<10",
                        "value": "x<10",
                        "link": {
                            "x": [str(i) for i in range(3, 10, 2)]
                        }
                    },
                    {
                        "id": 5,
                        "name": "10<=x<40",
                        "value": "10<=x<40",
                        "link": {
                            "x": [str(i) for i in range(11, 40, 2)]
                        }
                    },
                    {
                        "id": 6,
                        "name": "40<=x<80",
                        "value": "40<=x<80",
                        "link": {
                            "x": [str(i) for i in range(41, 80, 2)]
                        }
                    },
                    {
                        "id": 7,
                        "name": "80<=x<100",
                        "value": "80<=x<100",
                        "link": {
                            "x": [str(i) for i in range(81, 100, 2)]
                        }
                    }
                ],
                "filteredBy": ["label"],
                "filteredFor": ["x"]
            },
            {
                "filter": "x",
                "label": "X",
                "type": "choice",
                "values": x_values,
                "filteredBy": ["label", "sublabel"]
            }
        ]

    def get(self, label="x", sublabel="x", x=5, y=1, index=None, columns=None,
            **kwargs):
        """Generate a matrix based on x, y, z
        """
        x, y = int(x), int(y)
        df = pd.DataFrame(np.random.randint(1, 10, size=(x, y)),
                          columns=["label{}".format(i) for i in range(y)])
        if columns:
            df.columns = columns
        if index:
            df.set_index(index)
        return df
