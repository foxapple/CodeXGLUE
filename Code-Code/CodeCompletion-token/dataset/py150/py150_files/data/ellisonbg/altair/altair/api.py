"""
Main API for Vega-lite spec generation.

DSL mapping Vega types to IPython traitlets.

The inheritance of classes for Vega-lite spec in this file is as follows,
where Shelf*, DataCoordinate*, and FacetCoordinate* are not part of the
Vega-lite spec but are useful to follow DRY.

Shelf*
|
|_______________________________________________________________
|                   |                   |           |           |
DataCoordinate*     FacetCoordinate*    Shape       Color       Size
|                   |
|_______            |_______
|       |           |       |
X       Y           Row     Column
"""

try:
    import traitlets as T
    from traitlets.config import Configurable, Config
except ImportError:
    from IPython.utils import traitlets as T

from .utils import parse_shorthand, infer_vegalite_type, DataFrameTrait
from ._py3k_compat import string_types
from .renderer import Renderer

import pandas as pd




class BaseObject(Configurable):

    skip = []

    def __contains__(self, key):
        value = getattr(self, key)
        if isinstance(value, pd.DataFrame):
            return True
        return ((value is not None)
                and (not (not isinstance(value, bool) and not value)))

    def to_dict(self):
        result = {}
        for k in self.traits():
            if k in self and k not in self.skip:
                v = getattr(self, k)
                if v is not None:
                    if isinstance(v, BaseObject):
                        result[k] = v.to_dict()
                    else:
                        result[k] = v
        return result

    def __repr__(self):
        return repr(self.to_dict())


class Data(BaseObject):

    formatType = T.Enum(['json', 'csv'], default_value='json')
    url = T.Unicode(default_value=None, allow_none=True)
    values = T.List(default_value=None, allow_none=True)

    def to_dict(self):
        result = {'formatType': self.formatType,
                  'values': self.data.to_dict('records')}
        return result


class Scale(BaseObject):
    """Scale object that represents the Scale property common to: X, Y, Size, Color"""
    # TODO: Supported types for type
    # TODO: Supported types for reverse
    # TODO: Supported types for zero
    # TODO: Supported types for nice

    type = T.Enum(['linear', 'log', 'pow', 'sqrt', 'quantile'], default_value='linear')
    reverse = T.Bool(False)
    zero = T.Bool(True)
    nice = T.Enum(['second', 'minute', 'hour', 'day', 'week', 'month', 'year'], allow_none=True)
    useRawDomain = T.Bool(default_value=None, allow_none=True)


class ColorScale(Scale):
    """Scale object that adds additional properties to the Scale property for Color"""

    range = T.Union([T.Unicode(), T.List(T.Unicode)], default_value=None, allow_none=True)
    c10palette = T.Enum(['category10', 'category10k', 'Pastel1', 'Pastel2', 'Set1', 'Set2', 'Set3'],
                        default_value='category10')
    c20palette = T.Enum(['category20', 'category20b', 'category20c'], default_value='category20')
    ordinalPalette = T.Enum(['YlGn', 'YlGnBu', 'GnBu', 'BuGn', 'PuBuGn', 'PuBu', 'BuPu', 'RdPu', 'PuRd',
                             'OrRd', 'YlOrRd', 'YlOrBr', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',
                             'Greys', 'PuOr', 'BrBG', 'PRGn', 'PiYG', 'RdBu', 'RdGy', 'RdYlBu', 'Spectral',
                             'RdYlGn', 'Accent', 'Dark2', 'Paired', 'Pastel1', 'Pastel2', 'Set1', 'Set2', 'Set3'],
                            default_value='BuGn')


class Axis(BaseObject):

    grid = T.Bool(True)
    layer = T.Unicode(u'back')
    orient = T.Enum(['top', 'right', 'left', 'bottom'], default_value=None, allow_none=True)
    ticks = T.Int(5)
    title = T.Unicode(default_value=None, allow_none=True)
    titleMaxLength = T.Int(default_value=None, allow_none=True)
    titleOffset = T.Int(default_value=None, allow_none=True)
    format = T.Unicode(default_value=None, allow_none=True)
    maxLabelLength = T.Int(25, min=0)


class Band(BaseObject):

    size = T.Int(600, min=0)
    padding = T.Int(1, min=0)


class Bin(BaseObject):
    # TODO: Default should be 15 and minimum for maxbins

    maxbins = T.Int(0, config=True)


class SortItems(BaseObject):
    # TODO: Supported types for type
    # TODO: assert name and aggregate are required

    name = T.Unicode(default_value=None, allow_none=True)
    aggregate = T.Enum(['avg', 'sum', 'min', 'max', 'count'],
                       default_value=None, allow_none=True)
    reverse = T.Bool(False)


class Shelf(BaseObject):
    # TODO: Supported enums & supported types for aggregate
    # TODO: Supported types for timeunit
    # TODO: Supported types for bin
    # TODO: supported role?
    # TODO: supported mark types?
    # TODO: assert name and type are required

    skip = ['shorthand', 'config']

    def __init__(self, shorthand, **kwargs):
        kwargs['shorthand'] = shorthand
        super(Shelf, self).__init__(**kwargs)

    def _infer_type(self, data):
        if self.type is None and self.name in data:
            self.type = infer_vegalite_type(data[self.name])

    def _shorthand_changed(self, name, old, new):
        # TODO: if name of shorthand changed, should it reset all properties of obj?
        D = parse_shorthand(self.shorthand)
        for key, val in D.items():
            setattr(self, key, val)

    def to_dict(self):
        if not self.name:
            return None
        return super(Shelf, self).to_dict()

    shorthand = T.Unicode('')
    name = T.Unicode('', config=True)
    type = T.Enum(['N', 'O', 'Q', 'T'], default_value=None, allow_none=True,
                  config=True)
    timeUnit = T.Enum(['year', 'month', 'day', 'date',
                       'hours', 'minutes', 'seconds'],
                      default_value=None, allow_none=True)
    bin = T.Union([T.Bool(), T.Instance(Bin)], default_value=False)
    sort = T.List(T.Instance(SortItems), default_value=None, allow_none=True)
    aggregate = T.Enum(['avg', 'sum', 'median', 'min', 'max', 'count'],
                       default_value=None, allow_none=True, config=True)


class DataCoordinate(Shelf):
    scale = T.Instance(Scale, default_value=None, allow_none=True)
    axis = T.Instance(Axis, default_value=None, allow_none=True)
    band = T.Instance(Band, default_value=None, allow_none=True)


class X(DataCoordinate):
    shelf_name = 'x'


class Y(DataCoordinate):
    shelf_name = 'y'



class FacetCoordinate(Shelf):
    # TODO: supported types for aggregate
    # TODO: min and max for padding
    # TODO: min for height

    aggregate = T.Enum(['count'], default_value=None, allow_none=True)
    padding = T.CFloat(0.1)
    axis = T.Instance(Axis, default_value=None, allow_none=True)
    height = T.CInt(150)


class Row(FacetCoordinate):
    # TODO: supported role
    # TODO: required name and type - fulfilled when shelf does it
    # TODO: supportedMarkTypes
    shelf_name = 'row'



class Col(FacetCoordinate):
    shelf_name = 'col'


class Size(Shelf):
    # TODO: min for value
    # TODO: supported role
    # TODO: supported mark types
    shelf_name = 'size'
    scale = T.Instance(Scale, default_value=None, allow_none=True)
    legend = T.Bool(True)
    value = T.CInt(30)



class Color(Shelf):
    # TODO: default value for value should be 'steelblue'
    # TODO: min and max for opacity
    # TODO: supported role
    # TODO: supported mark types
    shelf_name = 'color'
    scale = T.Instance(ColorScale, default_value=None, allow_none=True)
    legend = T.Bool(True)
    value = T.Unicode('#4682b4')
    opacity = T.Float(1.0)


class Shape(Shelf):
    shelf_name = 'shape'
    value = T.Enum(['circle', 'square', 'cross', 'diamond', 'triangle-up',
                    'triangle-down'], default_value='circle')
    aggregate = T.Enum(['count'], default_value=None, allow_none=True)
    legend = T.Bool(True)
    filled = T.Bool(False)


class Font(BaseObject):
    weight = T.Enum(['normal', 'bold'], default_value='normal')
    size = T.Int(10, min=0)
    family = T.Unicode('Helvetica Neue')
    style = T.Enum(['normal', 'italic'], default_value='normal')


class Text(Shelf):
    shelf_name = 'text'
    scale = T.Instance(Scale, default_value=None, allow_none=True)
    align = T.Unicode('right')
    baseline = T.Unicode('middle')
    color = T.Unicode('#000000')
    margin = T.Int(4, min=0)
    placeholder = T.Unicode('Abc')
    font = T.Instance(Font, default_value=None, allow_none=True)
    format = T.Unicode(allow_none=True, default_value=None)


class Detail(Shelf):
    shelf_name = 'detail'
    aggregate = T.Enum(['count'], default_value=None, allow_none=True, config=True)


class Encoding(BaseObject):
    # TODO: add test and detail
    
    x = T.Union([T.Instance(X), T.Unicode()],
                default_value=None, allow_none=True)
    y = T.Union([T.Instance(Y), T.Unicode()],
                default_value=None, allow_none=True)
    row = T.Union([T.Instance(Row), T.Unicode()],
                  default_value=None, allow_none=True)
    col = T.Union([T.Instance(Col), T.Unicode()],
                  default_value=None, allow_none=True)
    size = T.Union([T.Instance(Size), T.Unicode()],
                   default_value=None, allow_none=True)
    color = T.Union([T.Instance(Color), T.Unicode()],
                    default_value=None, allow_none=True)
    shape = T.Union([T.Instance(Shape), T.Unicode()],
                    default_value=None, allow_none=True)
    detail = T.Union([T.Instance(Detail), T.Unicode()],
                     default_value=None, allow_none=True)
    text = T.Union([T.Instance(Text), T.Unicode()],
                   default_value=None, allow_none=True)

    parent = T.Instance(BaseObject, default_value=None, allow_none=True)

    skip = ['parent', 'config']

    def _infer_types(self, data):
        for attr in ['x', 'y', 'row', 'col', 'size', 'color', 'shape', 'detail', 'text']:
            val = getattr(self, attr)
            if val is not None:
                val._infer_type(data)

    def _x_changed(self, name, old, new):
        if isinstance(new, string_types):
            self.x = X(new, config=self.config)
        if getattr(self.parent, 'data', None) is not None:
            self.x._infer_type(self.parent.data)

    def _y_changed(self, name, old, new):
        if isinstance(new, string_types):
            self.y = Y(new, config=self.config)
        if getattr(self.parent, 'data', None) is not None:
            self.y._infer_type(self.parent.data)

    def _row_changed(self, name, old, new):
        if isinstance(new, string_types):
            self.row = Row(new)
        if getattr(self.parent, 'data', None) is not None:
            self.row._infer_type(self.parent.data)

    def _col_changed(self, name, old, new):
        if isinstance(new, string_types):
            self.col = Col(new)
        if getattr(self.parent, 'data', None) is not None:
            self.col._infer_type(self.parent.data)

    def _size_changed(self, name, old, new):
        if isinstance(new, string_types):
            self.size = Size(new)
        if getattr(self.parent, 'data', None) is not None:
            self.size._infer_type(self.parent.data)

    def _color_changed(self, name, old, new):
        if isinstance(new, string_types):
            self.color = Color(new)
        if getattr(self.parent, 'data', None) is not None:
            self.color._infer_type(self.parent.data)

    def _shape_changed(self, name, old, new):
        if isinstance(new, string_types):
            self.shape = Shape(new)
        if self.parent is not None:
            self.shape._infer_type(self.parent.data)

    def _detail_changed(self, name, old, new):
        if isinstance(new, string_types):
            self.detail = Detail(new)
        if self.parent is not None:
            self.detail._infer_type(self.parent.data)

    def _text_changed(self, name, old, new):
        if isinstance(new, string_types):
            self.text = Text(new)
        if self.parent is not None:
            self.text._infer_type(self.parent.data)


class Filter():
    # TODO: fill out

    pass


class ConfigVegaLite():
    # TODO: fill out

    pass


class VLConfig(BaseObject):

    width = T.Int(600)
    height = T.Int(400)
    singleWidth = T.Int(default_value=None, allow_none=True)
    singleHeight = T.Int(default_value=None, allow_none=True)
    gridColor = T.Unicode('black')
    gridOpacity = T.Float(0.08)


class Viz(BaseObject):

    marktype = T.Enum(['point', 'tick', 'bar', 'line',
                      'area', 'circle', 'square', 'text'],
                      default_value='point')
    encoding = T.Instance(Encoding, default_value=None, allow_none=True)
    vlconfig = T.Instance(VLConfig, allow_none=True)

    def _vlconfig_default(self):
        return VLConfig()

    _data = T.Instance(Data, default_value=None, allow_none=True)
    data = DataFrameTrait(default_value=None, allow_none=True)

    def _encoding_changed(self, name, old, new):
        if isinstance(new, Encoding):
            self.encoding.parent = self
            if 'data' in self:
                self.encoding._infer_types(self.data)

    def _data_changed(self, name, old, new):
        if not isinstance(new, pd.DataFrame):
            self.data = pd.DataFrame(new)
            return
        self._data = Data(data=new)
        if self.encoding is not None:
            self.encoding._infer_types(self.data)

    skip = ['data', '_data', 'vlconfig']

    def __init__(self, data, **kwargs):
        kwargs['data'] = data
        super(Viz, self).__init__(**kwargs)

    def to_dict(self):
        D = super(Viz, self).to_dict()
        D['data'] = self._data.to_dict()
        D['config'] = self.vlconfig.to_dict()
        return D

    def select_x(self, order=None):
        """
        Helper function that does a best effort of selecting an automatic x axis.

        Raises AssertionError if it cannot find a x axis to choose.
        """
        assert self.data is not None
        assert len(self.data) >= 1

        if order is None:
            order = ['T', 'O', 'N', 'Q']
        else:
            self._validate_custom_order(order)

        d = self._classify_data_by_type(order)

        chosen_x = None
        for typ in order:
            if len(d[typ]) >= 1:
                chosen_x = d[typ][0]
                break

        if chosen_x is None:
            raise ValueError('Could not select X.')

        if self.encoding is None:
            self.encoding = Encoding()

        self.encoding.x = chosen_x

    def select_y(self, order=None, aggregator=None):
        """
        Helper function that does a best effort of selecting an automatic y axis.
        It won't set the same axis that x is set to again, so X has to be set for the method to be called.

        Raises AssertionError if it cannot find a y axis to choose.
        """
        assert self.data is not None
        assert len(self.data) >= 2
        assert self.encoding is not None
        assert self.encoding.x is not None

        if order is None:
            order = ['Q', 'O', 'N', 'T']
        else:
            self._validate_custom_order(order)

        x_name = self.encoding.x.name
        d = self._classify_data_by_type(order, [x_name])

        # Choose the first column found on the following order: Q, O, N, T
        chosen_y = None
        for typ in order:
            if len(d[typ]) >= 1:
                chosen_y = d[typ][0]
                break

        if chosen_y is None:
            raise ValueError('Could not select Y.')

        # Use aggregator if specified
        if aggregator is not None:
            chosen_y = '{}({})'.format(aggregator, chosen_y)

        self.encoding.y = chosen_y

    def _validate_custom_order(self, order):
        assert len(order) == 4
        list_to_check = list(order)
        list_to_check.sort()
        assert list_to_check == ['N', 'O', 'Q', 'T']

    def _classify_data_by_type(self, order, skip=[]):
        """Get O, N, Q, or T vegalite type for all columns in data except if in skip."""
        d = dict()
        for typ in order:
            d[typ] = []

        for column_name in self.data:
            if column_name not in skip:
                typ = infer_vegalite_type(self.data[column_name])
                d[typ].append(column_name)

        return d

    def encode(self, **kwargs):
        self.encoding = Encoding(**kwargs)
        return self

    def configure(self, **kwargs):
        """Set chart configuration"""
        self.vlconfig = VLConfig(**kwargs)
        return self

    def set_single_dims(self, width, height):
        """
        Helper function for setting single-widths

        Parameters
        ----------
        width: int
        height: int
        """
        self.vlconfig.width = width
        self.vlconfig.height = height
        self.vlconfig.singleWidth = int(width * 0.75)
        self.vlconfig.singleHeight = int(height * 0.75)

        if self.encoding.x.type in ('N', 'O'):
            self.encoding.x.band = Band(size=int(width/10))

        if self.encoding.y.type in ('N', 'O'):
            self.encoding.y.band = Band(size=int(height/10))
        return self

    def mark(self, mt):
        """
        Set mark to given string value.

        Parameters
        ----------
        mt: str
        """
        self.marktype = mt
        return self

    def point(self):
        return self.mark('point')

    def tick(self):
        return self.mark('tick')

    def bar(self):
        return self.mark('bar')

    def line(self):
        return self.mark('line')

    def area(self):
        return self.mark('area')

    def circle(self):
        return self.mark('circle')

    def square(self):
        return self.mark('square')

    def text(self):
        return self.mark('text')

    def hist(self, bins=10, **kwargs):
        """
        Render histogram with given `bins`.

        Parameters
        ----------
        bins: int, default 10
        """

        self.marktype = "bar"

        config = Config()

        config.Y.type = "Q"
        config.Y.aggregate = "count"

        # We're making sure a y-change is triggered
        self.encoding = Encoding(config=config, y='', **kwargs)

        if isinstance(kwargs.get("x"), str):
            self.encoding.x.bin = Bin(maxbins=bins)

        # Hack: y.name should be "*", but version weirdness
        self.encoding.y.name = self.encoding.x.name

        return self

    def render(self, **kwargs):
        global _renderer
        return _renderer.render(self, **kwargs)


# Renderer logic

def _get_matplotlib_renderer():
    from .mpl import MatplotlibRenderer
    return MatplotlibRenderer()

def _get_lightning_renderer():
    from .lgn import LightningRenderer
    return LightningRenderer()

_renderers = {
    'matplotlib': _get_matplotlib_renderer,
    'lightning': _get_lightning_renderer
}


_renderer = None

def register_renderer(name, rfactory):
    """Register a renderer factory that creates renderer instances."""
    global _renderers
    _renderers[name] = rfactory

def use_renderer(r):
    """Use a particular renderer, registered by name or an actual Renderer instance."""
    global _renderer
    global _renderers
    if isinstance(r, Renderer):
        _renderer = r
    else:
        if r in _renderers:
            _renderer = _renderers[r]()
        else:
            raise ValueError('renderer could not be found: {0}').format(r)

def list_renderers():
    global _renderers
    return list(_renderers.keys())
