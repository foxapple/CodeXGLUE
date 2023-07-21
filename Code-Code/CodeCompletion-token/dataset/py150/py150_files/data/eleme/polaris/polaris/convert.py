"""
    polaris.convert
    ~~~~~~~~~~~~~~~

    :copyright: (c) 2013 Eleme, http://polaris.eleme.io
    :license: MIT

    Convert from DataFrame to other types for response.
"""

import datetime
import io
import json

from functools import reduce
from flask import current_app
from polaris.exc import InvalidSourceError
from .packages import echarts


def to_df(chart, **kwargs):
    """Convert chart to dataframe.
    """
    if chart.source not in current_app.config["source"]:
        raise InvalidSourceError(
            "Source not found: {}".format(chart.source))

    options = dict(chart.payload)
    options.update(kwargs)
    df = current_app.config["source"][chart.source].get(**options)
    df._metadata = {
        "name": chart.name,
        "description": chart.description,
    }
    return df


def to_geo(chart, **kwargs):
    """Convert chart to geo typed json.
    """
    if chart.source not in current_app.config["source"]:
        raise InvalidSourceError(
            "Source not found: {}".format(chart.source))

    options = dict(chart.payload)
    options.update(kwargs)
    geo = current_app.config["source"][chart.source].get(**options)
    geo["name"] = chart.name
    return geo


def to_data(df, data_type):
    """Convert dataframe to data.
    """
    data_type = data_type.strip().lower()

    if data_type == "csv":
        with io.StringIO() as csv:
            df.to_csv(csv)
            return csv.getvalue()

    elif data_type == "html":
        return df.to_html()

    elif data_type == "json":
        df.insert(0, 'idx', df.index.map(str))
        return df.to_json(orient="records", force_ascii=False)

    elif data_type == "table":
        idx = df.index
        if not df.empty and isinstance(idx[0], datetime.datetime):
            idx = idx.map(lambda x: x.strftime("%Y-%m-%d"))
        else:
            idx = idx.map(str)
        df.insert(0, 'idx', idx)

        res = {
            "columns": list(df.keys()),
            "values": json.loads(df.to_json(orient="records",
                                            force_ascii=False)),
            "metadata": df._metadata
        }

        return json.dumps(res)


def to_echarts(df, chart_type, **kwargs):
    title = df._metadata['name']
    description = df._metadata['description']
    chart = echarts.Echart(title=title, description=description)
    cls_maps = {
        'line': echarts.Line,
        'area': echarts.Line,
        'bar': echarts.Bar,
        'groupedbar': echarts.Bar,
        'pie': echarts.Pie,
        'scatter': echarts.Scatter,
        'radar': echarts.Radar,
        'force': echarts.Force,
        'chord': echarts.Chord,
        'map': echarts.Map,
    }
    assert chart_type in cls_maps

    idx = df.index
    if not df.empty and isinstance(idx[0], datetime.datetime):
        idx = idx.map(lambda x: x.strftime("%Y-%m-%d"))
    else:
        idx = idx.map(str)

    axis_style = {
        "axisLine": {"show": False}
    }
    tooltip_style = {
        "axisPointer": {
            "type": "line",
            "lineStyle": {"width": 1}
        }
    }

    if chart_type in ('line', 'area', 'bar', 'groupedbar', 'scatter'):
        gap = chart_type not in ('line', 'area')
        x_axis = echarts.Axis('category', 'bottom', data=list(idx), gap=gap,
                              **axis_style)
        y_axis = echarts.Axis('value', 'left', **axis_style)
        chart.use(x_axis)
        chart.use(y_axis)
        chart.use(echarts.Tooltip('axis', **tooltip_style))
    else:
        chart.use(echarts.Tooltip('item'))

    Type = cls_maps[chart_type]

    if chart_type == 'pie':
        data = []
        names = []
        if len(df.columns) == 1:
            title = df.columns[0]
            for name, value in zip(idx, df[title].data):
                data.append(dict(name=name, value=value))
                names.append(name)
        else:
            for name in df.columns:
                value = int(reduce(lambda x, y: x + y, df[name].data))
                name = str(name)
                data.append(dict(name=name, value=value))
                names.append(name)

        kwargs = {
            'radius': ['5%', '55%'],
            'center': ['50%', '50%'],
            'roseType': 'radius',
            'itemStyle': {
                'normal': {
                    'label': {'show': False},
                    'labelLine': {'show': False}
                }
            },
        }
        chart.use(Type(name=title, data=data, **kwargs))
        chart.use(echarts.Legend(data=names))
        return chart

    if chart_type in ('area', 'bar'):
        kwargs = {
            'stack': True,
            'itemStyle': {'normal': {'areaStyle': {'type': 'default'}}}
        }

    else:
        kwargs = {}

    for name in df.columns:
        data = list(df[name].data)

        if chart_type == 'scatter':
            data = list(zip(idx, data))
        chart.use(Type(name, data=data, **kwargs))

    return chart
