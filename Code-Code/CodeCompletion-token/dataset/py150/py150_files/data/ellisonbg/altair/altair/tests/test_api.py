import numpy as np
import pandas as pd
import numpy as np
import pandas as pd
from traitlets import TraitError
import pytest

from altair import api

from .. import api, spec


VALID_MARKTYPES = spec.SPEC['properties']['marktype']['enum']

def build_simple_spec():
    data = dict(x=[1, 2, 3],
                y=[4, 5, 6])
    return api.Viz(data), data


def test_empty_data():
    d = api.Data()
    assert d.formatType=='json'
    assert 'formatType' in d
    assert 'url' not in d
    assert 'values' not in d


def test_dict_data():
    spec, data = build_simple_spec()
    assert np.all(spec.data == pd.DataFrame(data))


def test_dataframe_data():
    spec, data = build_simple_spec()
    data = data = pd.DataFrame(data)
    spec = api.Viz(data)
    assert np.all(spec.data == data)


def test_to_dict():
    data = pd.DataFrame({'x': [1, 2, 3],
                         'y': [4, 5, 6]})
    spec = api.Viz(data).encode(x='x', y='y')

    D = spec.to_dict()

    assert D == {'config': {'gridColor': 'black',
                            'gridOpacity': 0.08,
                            'height': 400,
                            'width': 600},
                 'data': {'formatType': 'json',
                          'values': [{'x': 1, 'y': 4},
                                     {'x': 2, 'y': 5},
                                     {'x': 3, 'y': 6}]},
                 'encoding': {'x': {'bin': False, 'name': 'x', 'type': 'Q'},
                              'y': {'bin': False, 'name': 'y', 'type': 'Q'}},
                 'marktype': 'point'}


def test_vl_spec_for_scale_defaults():
    """Check that defaults are according to spec"""

    # This scale object is the property used for X, Y, Size
    scale = api.Scale()
    assert scale.type == 'linear'
    assert scale.reverse == False
    assert scale.zero == True
    assert scale.nice is None
    assert scale.useRawDomain is None

    # Scale object for property in Color
    scale = api.ColorScale()
    assert scale.type == 'linear'
    assert scale.reverse == False
    assert scale.zero == True
    assert scale.nice is None
    assert scale.useRawDomain is None
    assert scale.range is None
    assert scale.c10palette == 'category10'
    assert scale.c20palette == 'category20'
    assert scale.ordinalPalette == 'BuGn'


def test_vl_spec_for_scale_changes():
    """Check that changes are possible and sticky"""

    # This scale object is the property used for X, Y, Size
    scale = api.Scale(type='log', reverse=True, zero=False, nice='second', useRawDomain=True)
    assert scale.type == 'log'
    assert scale.reverse == True
    assert scale.zero == False
    assert scale.nice == 'second'
    assert scale.useRawDomain == True

    scale.type = 'linear'
    scale.reverse = False
    scale.zero = True
    scale.nice = None
    scale.useRawDomain = None
    assert scale.type == 'linear'
    assert scale.reverse == False
    assert scale.zero == True
    assert scale.nice is None
    assert scale.useRawDomain is None

    # Scale object for property in Color
    scale = api.ColorScale(type='log', reverse=True, zero=False, nice='second', useRawDomain=True,
                           range='category10', c10palette='Set1', c20palette='category20c', ordinalPalette='Spectral')
    assert scale.type == 'log'
    assert scale.reverse == True
    assert scale.zero == False
    assert scale.nice == 'second'
    assert scale.useRawDomain == True
    assert scale.range == 'category10'
    assert scale.c10palette == 'Set1'
    assert scale.c20palette == 'category20c'
    assert scale.ordinalPalette == 'Spectral'

    scale.range = ['category10']
    scale.c10palette = 'Set3'
    scale.c20palette = 'category20b'
    scale.ordinalPalette = 'Dark2'
    assert scale.range == ['category10']
    assert scale.c10palette == 'Set3'
    assert scale.c20palette == 'category20b'
    assert scale.ordinalPalette == 'Dark2'


def test_vl_spec_for_detail_defaults():
    """Check that defaults are according to spec"""

    detail = api.Detail('foobar')
    assert detail.name == 'foobar'
    assert detail.type is None
    assert detail.timeUnit is None
    assert detail.bin is False
    assert detail.sort == []
    assert detail.aggregate is None

    detail = api.Detail('foobar:O')
    assert detail.name == 'foobar'
    assert detail.type == 'O'
    assert detail.timeUnit is None
    assert detail.bin is False
    assert detail.sort == []
    assert detail.aggregate is None

    detail = api.Detail('count(foobar):O')
    assert detail.name == 'foobar'
    assert detail.type == 'O'
    assert detail.timeUnit is None
    assert detail.bin is False
    assert detail.sort == []
    assert detail.aggregate == 'count'


def test_vl_spec_for_detail_changes():
    """Check that changes are possible and sticky"""
    detail = api.Detail('foobar', type='O', timeUnit='minutes', bin=api.Bin(), sort=[api.SortItems()],
                        aggregate='count')
    assert detail.name == 'foobar'
    assert detail.type == 'O'
    assert detail.timeUnit == 'minutes'
    assert detail.bin.to_dict() == api.Bin().to_dict()
    assert detail.sort[0].to_dict() == api.SortItems().to_dict()
    assert detail.aggregate == 'count'

    detail.shorthand = 'count(foobar):Q'
    assert detail.name == 'foobar'
    assert detail.type == 'Q'
    assert detail.timeUnit == 'minutes'
    assert detail.bin.to_dict() == api.Bin().to_dict()
    assert detail.sort[0].to_dict() == api.SortItems().to_dict()
    assert detail.aggregate == 'count'


def test_vl_spec_for_detail_edge_values():
    """Check edge values"""
    detail = api.Detail('foobar')

    try:
        detail.shorthand = 'sum(foobar):O'
        raise Exception('Should have thrown for illegal aggregation value.')
    except TraitError:
        pass

    try:
        detail.aggregate = 'avg'
        raise Exception('Should have thrown for illegal aggregation value.')
    except TraitError:
        pass


def test_vl_spec_for_font_defaults():
    """Check that defaults are according to spec"""
    font = api.Font()
    assert font.weight == 'normal'
    assert font.size == 10
    assert font.family == 'Helvetica Neue'
    assert font.style == 'normal'


def test_vl_spec_for_font_changes():
    """Check that changes are possible and sticky"""
    font = api.Font(weight='bold', size=15, family='Serif', style='italic')
    assert font.weight == 'bold'
    assert font.size == 15
    assert font.family == 'Serif'
    assert font.style == 'italic'


def test_vl_spec_for_text_defaults():
    """Check that defaults are according to spec"""

    text = api.Text('foobar')
    assert text.name == 'foobar'
    assert text.type is None
    assert text.timeUnit is None
    assert text.bin is False
    assert text.sort == []
    assert text.aggregate is None
    assert text.scale is None
    assert text.align == 'right'
    assert text.baseline == 'middle'
    assert text.color == '#000000'
    assert text.margin == 4
    assert text.placeholder == 'Abc'
    assert text.font is None
    assert text.format is None

    text = api.Text('foobar:O')
    assert text.name == 'foobar'
    assert text.type == 'O'
    assert text.timeUnit is None
    assert text.bin is False
    assert text.sort == []
    assert text.aggregate is None
    assert text.scale is None
    assert text.align == 'right'
    assert text.baseline == 'middle'
    assert text.color == '#000000'
    assert text.margin == 4
    assert text.placeholder == 'Abc'
    assert text.font is None
    assert text.format is None

    text = api.Text('sum(foobar):O')
    assert text.name == 'foobar'
    assert text.type == 'O'
    assert text.timeUnit is None
    assert text.bin is False
    assert text.sort == []
    assert text.aggregate == 'sum'
    assert text.scale is None
    assert text.align == 'right'
    assert text.baseline == 'middle'
    assert text.color == '#000000'
    assert text.margin == 4
    assert text.placeholder == 'Abc'
    assert text.font is None
    assert text.format is None


def test_vl_spec_for_text_changes():
    """Check that changes are possible and sticky"""
    text = api.Text('foobar', type='O', timeUnit='minutes', bin=api.Bin(), sort=[api.SortItems()], aggregate='avg',
                    scale=api.Scale(), align='left', baseline='top', color='#111111', margin=3, placeholder = 'Aaa',
                    font=api.Font(), format='format')
    assert text.name == 'foobar'
    assert text.type == 'O'
    assert text.timeUnit == 'minutes'
    assert text.bin.to_dict() == api.Bin().to_dict()
    assert text.sort[0].to_dict() == api.SortItems().to_dict()
    assert text.aggregate == 'avg'
    assert text.scale.to_dict() == api.Scale().to_dict()
    assert text.align == 'left'
    assert text.baseline == 'top'
    assert text.color == '#111111'
    assert text.margin == 3
    assert text.placeholder == 'Aaa'
    assert text.font.to_dict() == api.Font().to_dict()
    assert text.format == 'format'

    text.shorthand = 'sum(foobar):Q'
    assert text.name == 'foobar'
    assert text.type == 'Q'
    assert text.timeUnit == 'minutes'
    assert text.bin.to_dict() == api.Bin().to_dict()
    assert text.sort[0].to_dict() == api.SortItems().to_dict()
    assert text.aggregate == 'sum'
    assert text.scale.to_dict() == api.Scale().to_dict()
    assert text.align == 'left'
    assert text.baseline == 'top'
    assert text.color == '#111111'
    assert text.margin == 3
    assert text.placeholder == 'Aaa'
    assert text.font.to_dict() == api.Font().to_dict()
    assert text.format == 'format'


def test_vl_spec_for_text_edge_values():
    """Check edge values"""
    text = api.Text('foobar')
    try:
        text.margin = -1
        raise Exception('Should have thrown for illegal margin min value.')
    except TraitError:
        pass


def test_vl_spec_for_axis_defaults():
    """Check that defaults are according to spec"""
    axis = api.Axis()
    assert axis.grid is True
    assert axis.layer == 'back'
    assert axis.orient is None
    assert axis.ticks == 5
    assert axis.title is None
    assert axis.titleMaxLength is None
    assert axis.titleOffset is None
    assert axis.format is None
    assert axis.maxLabelLength == 25


def test_vl_spec_for_axis_changes():
    """Check that changes are possible and sticky"""
    axis = api.Axis(grid=False, layer='front', orient='top', ticks=3, title='title', titleMaxLength=256, titleOffset=3,
                    format='format', maxLabelLength=3)
    assert axis.grid is False
    assert axis.layer == 'front'
    assert axis.orient == 'top'
    assert axis.ticks == 3
    assert axis.title == 'title'
    assert axis.titleMaxLength == 256
    assert axis.titleOffset == 3
    assert axis.format == 'format'
    assert axis.maxLabelLength == 3


def test_vl_spec_for_axis_edge_values():
    """Check edge values"""
    axis = api.Axis()
    try:
        axis.maxLabelLength = -1
        raise Exception('Should have thrown for illegal maxLabelLength min value.')
    except TraitError:
        pass


def test_vl_spec_for_band_defaults():
    """Check that defaults are according to spec"""

    band = api.Band()
    assert band.size == 600
    assert band.padding == 1


def test_vl_spec_for_band_changes():
    """Check that changes are possible and sticky"""

    band = api.Band(size=300, padding=15)
    assert band.size == 300
    assert band.padding == 15


def test_vl_spec_for_band_edge_values():
    """Check edge values"""

    band = api.Band()

    try:
        band.size = -1
        raise Exception('Should have thrown for illegal size min value.')
    except TraitError:
        pass

    try:
        band.padding = -1
        raise Exception('Should have thrown for illegal padding min value.')
    except TraitError:
        pass


def test_markers():
    spec, data = build_simple_spec()

    # call, e.g. spec.mark('point')
    for marktype in VALID_MARKTYPES:
        spec.mark(marktype)
        assert spec.marktype == marktype

    # call, e.g. spec.point()
    for marktype in VALID_MARKTYPES:
        method = marktype
        getattr(spec, method)()
        assert spec.marktype == marktype


def test_vl_spec_for_x_y__defaults():
    """Check that defaults are according to spec"""

    for x in [api.X('foobar'), api.Y('foobar')]:
        assert x.name == 'foobar'
        assert x.type is None       # TODO: None?! Spec says type is required
        assert x.aggregate is None
        assert x.timeUnit is None
        assert x.bin == False
        assert x.scale is None
        assert x.axis is None
        assert x.band is None
        assert x.sort == []

    for x in [api.X('foobar:O'), api.Y('foobar:O')]:
        assert x.name == 'foobar'
        assert x.type == 'O'
        assert x.aggregate is None
        assert x.timeUnit is None
        assert x.bin == False
        assert x.scale is None
        assert x.axis is None
        assert x.band is None
        assert x.sort == []

    for x in [api.X('sum(foobar):Q'), api.Y('sum(foobar):Q')]:
        assert x.name == 'foobar'
        assert x.type == 'Q'
        assert x.aggregate == 'sum'
        assert x.timeUnit is None
        assert x.bin == False
        assert x.scale is None
        assert x.axis is None
        assert x.band is None
        assert x.sort == []


def test_vl_spec_for_x_y_changes():
    """Check that changes are possible and sticky"""
    for x in [api.X('foobar:O', type='N', aggregate='median', timeUnit='seconds', bin=api.Bin(), scale = api.Scale(),
                    axis=api.Axis(), band=api.Band(), sort=[api.SortItems()]),
              api.Y('foobar:O', type='N', aggregate='median', timeUnit='seconds', bin=api.Bin(), scale = api.Scale(),
                    axis=api.Axis(), band=api.Band(), sort=[api.SortItems()])]:
        assert x.name == 'foobar'
        assert x.type == 'N'
        assert x.aggregate == 'median'
        assert x.timeUnit == 'seconds'
        assert x.bin.to_dict() == api.Bin().to_dict()
        assert x.scale.to_dict() == api.Scale().to_dict()
        assert x.axis.to_dict() == api.Axis().to_dict()
        assert x.band.to_dict() == api.Band().to_dict()
        assert x.sort[0].to_dict() == api.SortItems().to_dict()

        x.shorthand = 'sum(foobar):Q'
        assert x.name == 'foobar'
        assert x.type == 'Q'
        assert x.aggregate == 'sum'
        assert x.timeUnit == 'seconds'
        assert x.bin.to_dict() == api.Bin().to_dict()
        assert x.scale.to_dict() == api.Scale().to_dict()
        assert x.axis.to_dict() == api.Axis().to_dict()
        assert x.band.to_dict() == api.Band().to_dict()
        assert x.sort[0].to_dict() == api.SortItems().to_dict()


def test_vl_spec_for_size__defaults():
    """Check that defaults are according to spec"""
    size = api.Size('foobar')
    assert size.name == 'foobar'
    assert size.type is None
    assert size.aggregate is None
    assert size.timeUnit is None
    assert size.bin == False
    assert size.scale is None
    assert size.legend == True
    assert size.value == 30
    assert size.sort == []

    size = api.Size('foobar:O')
    assert size.name == 'foobar'
    assert size.type == 'O'
    assert size.aggregate is None
    assert size.timeUnit is None
    assert size.bin == False
    assert size.scale is None
    assert size.legend == True
    assert size.value == 30
    assert size.sort == []

    size = api.Size('sum(foobar):Q')
    assert size.name == 'foobar'
    assert size.type == 'Q'
    assert size.aggregate == 'sum'
    assert size.timeUnit is None
    assert size.bin == False
    assert size.scale is None
    assert size.legend == True
    assert size.value == 30
    assert size.sort == []


def test_vl_spec_for_size_changes():
    """Check that changes are possible and sticky"""
    size = api.Size('foobar', type='Q', aggregate='sum', timeUnit='minutes', bin=api.Bin(), scale=api.Scale(),
                    legend=False, value=0, sort=[api.SortItems()])
    assert size.name == 'foobar'
    assert size.type == 'Q'
    assert size.aggregate == 'sum'
    assert size.timeUnit == 'minutes'
    assert size.bin.to_dict() == api.Bin().to_dict()
    assert size.scale.to_dict() == api.Scale().to_dict()
    assert size.legend == False
    assert size.value == 0
    assert size.sort[0].to_dict() == api.SortItems().to_dict()

    size.shorthand = 'avg(foobar):O'
    assert size.name == 'foobar'
    assert size.type == 'O'
    assert size.aggregate == 'avg'
    assert size.timeUnit == 'minutes'
    assert size.bin.to_dict() == api.Bin().to_dict()
    assert size.scale.to_dict() == api.Scale().to_dict()
    assert size.legend == False
    assert size.value == 0
    assert size.sort[0].to_dict() == api.SortItems().to_dict()


def test_vl_spec_for_color__defaults():
    """Check that defaults are according to spec"""
    color = api.Color('foobar')
    assert color.name == 'foobar'
    assert color.type is None
    assert color.aggregate is None
    assert color.timeUnit is None
    assert color.bin == False
    assert color.scale is None
    assert color.legend == True
    assert color.value == '#4682b4'
    assert color.opacity == 1.0

    color = api.Color('foobar:O')
    assert color.name == 'foobar'
    assert color.type == 'O'
    assert color.aggregate is None
    assert color.timeUnit is None
    assert color.bin == False
    assert color.scale is None
    assert color.legend == True
    assert color.value == '#4682b4'
    assert color.opacity == 1.0

    color = api.Color('sum(foobar):Q')
    assert color.name == 'foobar'
    assert color.type == 'Q'
    assert color.aggregate == 'sum'
    assert color.timeUnit is None
    assert color.bin == False
    assert color.scale is None
    assert color.legend == True
    assert color.value == '#4682b4'
    assert color.opacity == 1.0


def test_vl_spec_for_color_changes():
    """Check that changes are possible and sticky"""
    color = api.Color('foobar', type='O', aggregate='avg', timeUnit='minutes', bin=api.Bin(), scale=api.ColorScale(),
                      legend=False, value='Dark2', opacity=0.5)
    assert color.name == 'foobar'
    assert color.type == 'O'
    assert color.aggregate == 'avg'
    assert color.timeUnit == 'minutes'
    assert color.bin.to_dict() == api.Bin().to_dict()
    assert color.scale.to_dict() == api.ColorScale().to_dict()
    assert color.legend == False
    assert color.value == 'Dark2'
    assert color.opacity == 0.5

    color.shorthand = 'sum(foobar):Q'
    assert color.name == 'foobar'
    assert color.type == 'Q'
    assert color.aggregate == 'sum'
    assert color.timeUnit == 'minutes'
    assert color.bin.to_dict() == api.Bin().to_dict()
    assert color.scale.to_dict() == api.ColorScale().to_dict()
    assert color.legend == False
    assert color.value == 'Dark2'
    assert color.opacity == 0.5


def test_encode():
    data = dict(col1=[1.0, 2.0, 3.0],
                col2=[0.1, 0.2, 0.3],
                col3=['A', 'B', 'C'],
                col4=[True, False, True],
                col5=[0.1, 0.2, 0.3],
                col6=pd.date_range('2012', periods=3, freq='A'),
                col7=np.arange(3),
                col8=np.arange(3),
                col9=np.arange(3))
    kwargs = dict(x='col1', y='col2', row='col3', col='col4',
                  size='col5', color='col6', shape='col7', text='col8', detail='col9')

    spec = api.Viz(data).encode(**kwargs)
    for key, name in kwargs.items():
        assert getattr(spec.encoding, key).name == name


def test_select_x():
    def _check(data, expected):
        v = api.Viz(data)
        v.select_x()
        assert v.encoding.x.name == expected

    data = dict(col1=[1.0, 2.0, 3.0],  # Q
                col2=['A', 'B', 'C'],  # N
                col3=pd.date_range('2012', periods=3, freq='A'),  # T
                col4=pd.date_range('2012', periods=3, freq='A'))  # T
    _check(data, 'col3')

    data = dict(col1=[1.0, 2.0, 3.0],  # Q
                col2=['A', 'B', 'C'],  # N
                col3=['A', 'B', 'C'])  # N
    _check(data, 'col2')

    data = dict(col1=[1.0, 2.0, 3.0],  # Q
                col2=np.arange(3))     # Q
    _check(data, 'col1')

    # No data
    with pytest.raises(AssertionError):
        v = api.Viz(None)
        v.select_x()

    # Empty data
    with pytest.raises(AssertionError):
        v = api.Viz(dict())
        v.select_x()

    # Custom order
    data = dict(col1=[1.0, 2.0, 3.0],  # Q
                col2=['A', 'B', 'C'],  # N
                col3=pd.date_range('2012', periods=3, freq='A'),  # T
                col4=pd.date_range('2012', periods=3, freq='A'))  # T
    v = api.Viz(data)
    v.select_x(['N', 'T', 'Q', 'O'])
    assert v.encoding.x.name == 'col2'


def test_select_y():
    def _check(data, expected, aggregator=None):
        v = api.Viz(data)
        v.encode()
        v.encoding.x = 'col1'
        if aggregator is None:
            v.select_y()
            assert v.encoding.y.name == expected
        else:
            v.select_y(None, aggregator)
            assert v.encoding.y.name == expected
            assert v.encoding.y.aggregate == aggregator

    data = dict(col1=[1.0, 2.0, 3.0],  # Chosen X
                col2=['A', 'B', 'C'],  # N
                col3=pd.date_range('2012', periods=3, freq='A'),  # T
                col4=pd.date_range('2012', periods=3, freq='A'),  # T
                col5=[1.0, 2.0, 3.0],  # Q
                col6=[1.0, 2.0, 3.0])  # Q
    _check(data, 'col5')
    _check(data, 'col5', 'avg')

    data = dict(col1=[1.0, 2.0, 3.0],  # Chosen X
                col2=['A', 'B', 'C'],  # N
                col3=pd.date_range('2012', periods=3, freq='A'),  # T
                col4=['A', 'B', 'C'])  # N
    _check(data, 'col2')
    _check(data, 'col2', 'sum')

    data = dict(col1=[1.0, 2.0, 3.0],  # Chosen X
                col2=pd.date_range('2012', periods=3, freq='A'),  # T
                col3=pd.date_range('2012', periods=3, freq='A'))  # T
    _check(data, 'col2')
    _check(data, 'col2', 'sum')

    # No data
    with pytest.raises(AssertionError):
        v = api.Viz(None)
        v.select_y()

    # Just one column
    with pytest.raises(AssertionError):
        v = api.Viz(dict(col1=[1.0,2.0]))
        v.select_y()

    # No encoding
    with pytest.raises(AssertionError):
        v = api.Viz(dict(col1=[1.0,2.0], col2=[1.0,2.0]))
        v.select_y()

    # No X
    with pytest.raises(AssertionError):
        v = api.Viz(dict(col1=[1.0,2.0], col2=[1.0,2.0]))
        v.encode()
        v.select_y()

    # Custom order
    data = dict(col1=[1.0, 2.0, 3.0],  # Chosen X
                col2=['A', 'B', 'C'],  # N
                col3=pd.date_range('2012', periods=3, freq='A'),  # T
                col4=pd.date_range('2012', periods=3, freq='A'),  # T
                col5=[1.0, 2.0, 3.0],  # Q
                col6=[1.0, 2.0, 3.0])  # Q
    v = api.Viz(data)
    v.encode()
    v.encoding.x = 'col1'
    v.select_y(['N', 'T', 'Q', 'O'])
    assert v.encoding.y.name == 'col2'


def test_encode_aggregates():
    data = dict(col1=[1.0, 2.0, 3.0],
                col2=[0.1, 0.2, 0.3],
                col3=['A', 'B', 'C'],
                col4=[True, False, True],
                col5=[0.1, 0.2, 0.3],
                col6=pd.date_range('2012', periods=3, freq='A'),
                col7=np.arange(3),
                col8=np.arange(3),
                col9=np.arange(3))
    kwargs = dict(x=('count', 'col1'), y=('count', 'col2'),
                  row=('count', 'col3'), col=('count', 'col4'),
                  size=('avg', 'col5'), color=('max', 'col6'),
                  shape=('count', 'col7'), text=('avg', 'col8'),
                  detail=('count', 'col9'))

    spec = api.Viz(data).encode(**{key:"{0}({1})".format(*val)
                                   for key, val in kwargs.items()})
    for key, val in kwargs.items():
        agg, name = val
        assert getattr(spec.encoding, key).name == name
        assert getattr(spec.encoding, key).aggregate == agg


def test_encode_types():
    data = dict(col1=[1.0, 2.0, 3.0],
                col2=[0.1, 0.2, 0.3],
                col3=['A', 'B', 'C'],
                col4=[True, False, True],
                col5=[0.1, 0.2, 0.3],
                col6=pd.date_range('2012', periods=3, freq='A'),
                col7=np.arange(3),
                col8=np.arange(3),
                col9=np.arange(3))
    kwargs = dict(x=('col1', 'Q'), y=('col2', 'Q'),
                  row=('col3', 'O'), col=('col4', 'N'),
                  size=('col5', 'Q'), color=('col6', 'T'),
                  shape=('col7', 'O'), text=('col8', 'O'),
                  detail=('col9', 'Q'))

    spec = api.Viz(data).encode(**{key:"{0}:{1}".format(*val)
                                   for key, val in kwargs.items()})
    for key, val in kwargs.items():
        name, typ = val
        assert getattr(spec.encoding, key).name == name
        assert getattr(spec.encoding, key).type == typ


def test_infer_types():
    data = dict(col1=[1.0, 2.0, 3.0],
                col2=[0.1, 0.2, 0.3],
                col3=['A', 'B', 'C'],
                col4=[True, False, True],
                col5=[0.1, 0.2, 0.3],
                col6=pd.date_range('2012', periods=3, freq='A'),
                col7=np.arange(3),
                col8=np.arange(3),
                col9=np.arange(3))
    kwargs = dict(x=('col1', 'Q'), y=('col2', 'Q'),
                  row=('col3', 'N'), col=('col4', 'N'),
                  size=('col5', 'Q'), color=('col6', 'T'),
                  shape=('col7', 'Q'), text=('col8', 'Q'),
                  detail=('col9', 'Q'))

    spec = api.Viz(data).encode(**{key: val[0]
                                   for key, val in kwargs.items()})
    for key, val in kwargs.items():
        name, typ = val
        assert getattr(spec.encoding, key).name == name
        assert getattr(spec.encoding, key).type == typ


def test_configure():
  spec, data = build_simple_spec()
  spec.configure(height=100, width=200)
  res = spec.to_dict()
  assert res['config']['height'] == 100
  assert res['config']['width'] == 200


def test_single_dim_setting():
    spec, data = build_simple_spec()
    spec.encode(x="x:N", y="y:Q").set_single_dims(100, 100)
    res = spec.to_dict()

    assert res['config']['width'] == 100
    assert res['config']['height'] == 100
    assert res['config']['singleWidth'] == 75
    assert res['config']['singleHeight'] == 75

    assert res['encoding']['x']['band']['size'] == 10
    assert res['encoding']['y'].get('band') is None


def test_hist():
    data = dict(x=[1, 2, 3],
                y=[4, 5, 6])

    viz1 = api.Viz(data).hist(x='x')
    assert viz1.encoding.x.name == "x"
    assert viz1.encoding.x.bin.maxbins == 10
    assert viz1.encoding.y.name == "x"
    assert viz1.encoding.y.type == "Q"
    assert viz1.encoding.y.aggregate == "count"

    viz2 = api.Viz(data).hist(x="x", bins=30)
    assert viz2.encoding.x.bin.maxbins == 30
    expected = {'config': {'gridColor': 'black',
                           'gridOpacity': 0.08,
                           'height': 400,
                           'width': 600},
                'data': {'formatType': 'json',
                         'values': [{'x': 1, 'y': 4},
                                    {'x': 2, 'y': 5},
                                    {'x': 3, 'y': 6}]},
                'encoding': {'x': {'bin': {'maxbins': 30},
                                   'name': 'x',
                                   'type': 'Q'},
                             'y': {'aggregate': 'count',
                                   'bin': False,
                                   'name': 'x',
                                   'type': 'Q'}},
                 'marktype': 'bar'}

    assert viz2.to_dict() == expected

    viz3 = api.Viz(data).hist(x="x:O",
        color=api.Color(shorthand="bar", type="N")
    )
    assert viz3.encoding.x.name == "x"
    assert viz3.encoding.x.type == "O"

    expected = {'config': {'gridColor': 'black',
                           'gridOpacity': 0.08,
                           'height': 400,
                           'width': 600},
                'data': {'formatType': 'json',
                'values': [{'x': 1, 'y': 4}, {'x': 2, 'y': 5},
                           {'x': 3, 'y': 6}]},
                'encoding': {'x': {'bin': {'maxbins': 10},
                                   'name': 'x', 'type': 'O'},
                             'y': {'aggregate': 'count',
                                   'bin': False,
                                   'name': 'x',
                                   'type': 'Q'},
                             'color': {'bin': False,
                                       'name': 'bar',
                                       'opacity': 1.0,
                                       'type': 'N',
                                       'value': '#4682b4',
                                       'legend': True}},
                'marktype': 'bar'}


    assert viz3.to_dict() == expected

    viz4 = api.Viz(data).hist(
        x=api.X(shorthand="x", bin=api.Bin(maxbins=40)))
    assert viz4.encoding.x.name == "x"
    assert viz4.encoding.x.bin.maxbins == 40
