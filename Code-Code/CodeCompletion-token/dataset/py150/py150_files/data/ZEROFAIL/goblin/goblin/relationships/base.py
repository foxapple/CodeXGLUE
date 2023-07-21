from __future__ import unicode_literals
import logging
import warnings
from functools import wraps

from goblin import connection
from goblin._compat import array_types, string_types
from goblin.tools import LazyImportClass
from goblin.exceptions import GoblinRelationshipException

from goblin.constants import IN, OUT, BOTH

logger = logging.getLogger(__name__)


def requires_vertex(method):
    @wraps(method)
    def method_wrapper(self, *args, **kwargs):
        if self.top_level_vertex:
            return method(self, *args, **kwargs)
        else:
            raise GoblinRelationshipException("No Vertex Instantiated")
    return method_wrapper


class Relationship(object):

    """
    Define incoming and outgoing relationships that exist. Also enforce
    schema IN, OUT and BOTH directions

    Warn if queries return schema violations.
    """

    def __init__(self, edge_class, vertex_class, direction=BOTH, strict=True,
                 gremlin_path=None, vertex_callback=None, edge_callback=None,
                 query_callback=None, create_callback=None):
        from goblin.models import Edge, Vertex
        self.edge_classes = self._create_class_tuple(
            edge_class, enforce_type=Edge)
        self.vertex_classes = self._create_class_tuple(
            vertex_class, enforce_type=Vertex)
        assert direction in (IN, OUT, BOTH), \
            "Direction of Relationship must be of one in (%s, %s, %s)" % (
                IN, OUT, BOTH)
        self.direction = direction
        self.strict = strict
        if gremlin_path:  # pragma: no cover
            self.gremlin_path = gremlin_path
        self.vertex_callback = vertex_callback
        self.edge_callback = edge_callback
        self.query_callback = query_callback
        self.create_callback = create_callback
        self.top_level_vertex_class = None
        self.top_level_vertex = None

    def _setup_instantiated_vertex(self, vertex):
        self.top_level_vertex = vertex
        self.top_level_vertex_class = vertex.__class__

    def _create_class_tuple(self, model_class, enforce_type=None):
        """
        Take in an string, array of classes, or a single class and make a
        tuple of said referenced classes

        :param model_class: Input to be transformed into reference class(es)
        :type model_class: string_types | array_types | goblin.models.Edge |
            goblin.models.Vertex
        :param enforce_type: Enforce a specific model type? If not provided,
            everything that is resolved passes, otherwise if a type is given,
            the classes are filtered out that don't match.
        :type enforce_type: None | goblin.models.Vertex | goblin.models.Edge
        :rtype: tuple[enforce_type | Object]
        """
        if isinstance(model_class, string_types):
            model_classes = (LazyImportClass(model_class), )
        elif isinstance(model_class, array_types):
            model_classes = []
            for mc in model_class:
                if isinstance(mc, string_types):
                    model_classes.append(LazyImportClass(mc))
                else:
                    model_classes.append(mc)
            model_classes = tuple(model_classes)
        else:
            model_classes = (model_class, )

        if not enforce_type:
            return model_classes
        else:
            final_classes = []
            for kls in model_classes:
                if (isinstance(kls, LazyImportClass) or
                        issubclass(kls, enforce_type)):
                    final_classes.append(kls)
                else:
                    warnings.warn(
                        "Relationship constraint is not derived from %s and will be ignored!" % enforce_type,
                        category=SyntaxWarning)
            return tuple(final_classes)

    @requires_vertex
    def vertices(self, limit=None, offset=None, callback=None, **kwargs):
        """ Query and return all Vertices attached to the current Vertex

        TODO: fix this, the instance method isn't properly setup
        :param limit: Limit the number of returned results
        :type limit: int | long
        :param offset: Query offset of the number of paginated results
        :type offset: int | long
        :param callback: (Optional) Callback function to handle results
        :type callback: method
        :rtype: List[goblin.models.Vertex] | Object
        """
        allowed_elts = []
        allowed_vlts = []
        for e in self.edge_classes:
            allowed_elts += [e.get_label()]
        for v in self.vertex_classes:
            allowed_vlts += [v.get_label()]

        if limit is not None and offset is not None:
            start = offset
            end = offset + limit
        else:
            start = end = None

        operation = self.direction.lower() + 'V'
        future_class = kwargs.get('future_class', None)
        if future_class is None:
            future_class = connection._future

        future = future_class()
        future_result = getattr(
            self.top_level_vertex, operation)(*allowed_elts)

        def on_vertices(f):
            try:
                result = f.result()
            except Exception as e:
                future.set_exception(e)
            else:
                if callback:
                    result = callback(result)
                elif self.vertex_callback:
                    result = self.vertex_callback(result)
                future.set_result(result)

        future_result.add_done_callback(on_vertices)

        return future

    @requires_vertex
    def edges(self, limit=None, offset=None, callback=None, **kwargs):
        """ Query and return all Edges attached to the current Vertex

        TODO: fix this, the instance method isn't properly setup
        :param limit: Limit the number of returned results
        :type limit: int | long
        :param offset: Query offset of the number of paginated results
        :type offset: int | long
        :param callback: (Optional) Callback function to handle results
        :type callback: method
        :rtype: List[goblin.models.Edge] | Object
        """
        allowed_elts = []
        for e in self.edge_classes:
            allowed_elts += [e.get_label()]

        if limit is not None and offset is not None:
            start = offset
            end = offset + limit
        else:
            start = end = None

        operation = self.direction.lower() + 'E'
        future_class = kwargs.get('future_class', None)
        if future_class is None:
            future_class = connection._future

        future = future_class()
        future_result = getattr(
            self.top_level_vertex, operation)(*allowed_elts)

        def on_edges(f):
            try:
                result = f.result()
            except Exception as e:
                future.set_exception(e)
            else:
                if callback:
                    result = callback(result)
                elif self.edge_callback:
                    result = self.edge_callback(result)
                future.set_result(result)

        future_result.add_done_callback(on_edges)

        return future

    def allowed(self, edge_type, vertex_type):
        """
        Check whether or not the allowed Edge and Vertex type are
        compatible with the schema defined

        :param edge_type: Edge Class
        :type: goblin.models.Edge
        :param vertex_type: Vertex Class
        :type: goblin.models.Vertex
        :rtype: bool
        """
        if self.strict:
            if (edge_type in self.edge_classes and
                    vertex_type in self.vertex_classes):
                return True
            else:
                return False
        else:
            return True

    @requires_vertex
    def query(self, edge_types=None, callback=None):
        """ Generic Query method for quick access

        :param edge_types: List of Edge classes to query against
        :type edge_types: List[goblin.models.Edge] | None
        :param callback: (Optional) Callback function to handle results
        :type callback: method
        :rtype: goblin.models.query.Query | Object
        """
        # if not self.top_level_vertex:
        #    raise GoblinRelationshipException("No vertex known to start with, this is an error")
        if edge_types:
            if not isinstance(edge_types, array_types):
                edge_types = (edge_types, )
            for et in edge_types:
                if et not in self.edge_classes:
                    raise GoblinRelationshipException(
                        "Not a recognized edge label type, invalid schema")
        else:
            edge_types = self.edge_classes
        from goblin.models.query import Query
        query = Query(self.top_level_vertex).labels(*edge_types)
        if callback:
            return callback(query)
        elif self.query_callback:
            return self.query_callback(query)
        else:
            return query

    def _create_entity(self, model_cls, model_params, outV=None, inV=None):
        """ Create Vertex and Edge between current Vertex and New Vertex

        :param model_cls: Vertex or Edge Class for the relationship
        :type model_cls: goblin.models.Vertex | goblin.models.Edge
        :param model_params: Vertex or Edge class parameters for instantiating
            the model
        :type model_params: dict
        :param outV: Outgoing Vertex if creating an Edge between two vertices
            (otherwise ignored)
        :type outV: goblin.models.Vertex
        :param inV: Incoming Vertex if creating an Edge between two vertices
            (otherwise ignored)
        :type inV: goblin.models.Vertex
        :rtype: goblin.models.Vertex | goblin.models.Edge
        """
        if isinstance(model_cls, LazyImportClass):
            model_cls = model_cls.klass

        create_cls = model_cls._get_factory()

        from goblin.models.edge import Edge
        if issubclass(model_cls, Edge):
            return create_cls(outV=outV, inV=inV, **model_params)
        else:
            return create_cls(**model_params)

    @requires_vertex
    def create(self, edge_params={}, vertex_params={}, edge_type=None,
               vertex_type=None, callback=None, **kwargs):
        """ Creates a Relationship defined by the schema

        :param edge_params: (Optional) Parameters passed to the instantiation
            method of the Edge
        :type edge_params: dict
        :param vertex_params: (Optional) Parameters passed to the instantiation
            method
        :type vertex_params: dict
        :param edge_type: (Optional) Edge class type, otherwise it defaults to
            the first Edge type known
        :type edge_type: goblin.models.Edge | None
        :param edge_type: (Optional) Vertex class type, otherwise it defaults
            to the first Vertex type known
        :type edge_type: goblin.models.Vertex | None
        :param callback: (Optional) Callback function to handle results
        :type callback: method
        :rtype: tuple(goblin.models.Edge, goblin.models.Vertex) | Object
        """
        # if not self.top_level_vertex:
        #    raise GoblinRelationshipException("No existing vertex known, haveyou created a vertex?")
        if not vertex_type:
            vertex_type = self.vertex_classes[0]
        if not edge_type:
            edge_type = self.edge_classes[0]
        if not self.allowed(edge_type, vertex_type):
            raise GoblinRelationshipException(
                "That is not a valid relationship setup: %s <-%s-> %s" % (
                    edge_type, self.direction, vertex_type))

        future_class = kwargs.get('future_class', None)
        if future_class is None:
            future_class = connection._future

        future = future_class()
        if isinstance(vertex_type, string_types):

            top_level_module = self.top_level_vertex.__module__
        new_vertex_future = self._create_entity(vertex_type, vertex_params)

        def on_vertex(f):
            try:
                new_vertex = f.result()
            except Exception as e:
                future.set_exception(e)
            else:
                if self.direction == IN:
                    outV = new_vertex
                    inV = self.top_level_vertex
                else:
                    outV = self.top_level_vertex
                    inV = new_vertex

                new_edge_future = self._create_entity(
                    edge_type, edge_params, outV=outV, inV=inV)

                def on_edge(f2):
                    try:
                        new_edge = f2.result()
                    except Exception as e:
                        future.set_exception(e)
                    else:
                        if callback:
                            try:
                                result = callback(new_edge, new_vertex)
                            except Exception as e:
                                future.set_exception(e)
                        elif self.create_callback:
                            try:
                                result = self.create_callback(
                                    new_edge, new_vertex)
                            except Exception as e:
                                future.set_exception(e)
                        else:
                            result = (new_edge, new_vertex)
                        future.set_result(result)

                new_edge_future.add_done_callback(on_edge)

        new_vertex_future.add_done_callback(on_vertex)

        return future
