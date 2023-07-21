from __future__ import absolute_import

import os
import json
import hashlib

import rdflib
import requests
from celery import Celery
from flask import Flask, make_response
from flask.ext.restful import Api, Resource, reqparse

from niquery.utils import NS
from niquery.query import AskQuery, SelectQuery


def create_app(environment=None):
    """
    Creates and configures the app depending on the environment indicated, which can be
    set explicitly or using the FLASK_CONFIG environment variable.

    Environments
    ------------
     - config
     - development (default)
     - production
     - docker
     - testing
    """
    app = Flask(__name__)

    if not environment:
        environment = os.environ.get('FLASK_CONFIG')
    if not environment:
        environment = 'development'

    app.config.from_object(
        'niquery.config.{}'.format(environment.capitalize()))

    return app


def make_celery(app):
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery


app = create_app()
api = Api(app)

@api.representation('text/turtle')
def turtle(data, code, headers=None):
    g = rdflib.ConjunctiveGraph()  # json-ld parsing works with conjunctive
    g.parse(data=json.dumps(data), format='json-ld')
    resp = make_response(g.serialize(format='turtle'), code)
    resp.headers.extend(headers or {})
    return resp

celery = make_celery(app)

@celery.task(name="tasks.add")
def add(x, y):
    return x + y

@celery.task(name='tasks.bet')
def bet(record):
    import nipype
    from nipype.interfaces.fsl import BET
    from nipype.utils.filemanip import hash_infile

    nipype.config.enable_provenance()

    in_file_uri = record['t1_uri']
    os.chdir('/tmp')
    fname = 'anatomy.nii.gz'

    with open(fname, 'wb') as fd:
        response = requests.get(in_file_uri, stream=True)
        if not response.ok:
            response.raise_for_status()
        for chunk in response.iter_content(1024):
            fd.write(chunk)

    # Check if interface has run with this input before
    sha = hash_infile(os.path.abspath(fname), crypto=hashlib.sha512)
    select = SelectQuery(config=app.config)
    res = select.execute_select('E0921842-1EDB-49F8-A4B3-BA51B85AD407')
    sha_recs = res[res.sha512.str.contains(sha)]
    bet_recs = res[res.interface.str.contains('BET')]
    results = dict()
    if sha_recs.empty or \
            (not sha_recs.empty and bet_recs.empty):
        better = BET()
        better.inputs.in_file = os.path.abspath(fname)
        result = better.run()
        prov = result.provenance.rdf().serialize(format='json-ld')
        results.update({'prov': prov})
    else:
        results.update({'prov': res.to_json(orient='records')})
    return results

parser = reqparse.RequestParser()
parser.add_argument('turtle_file')
parser.add_argument('query_uuid')


class Validate(Resource):
    def get(self):
        """
        Returns a list of queries used for validation of NIDM queries.
        """
        ask = AskQuery()
        return ask.sparql_meta.to_dict(outtype='records')


class ValidateResult(Resource):
    def get(self, task_id):
        """
        Returns the raw query text of a given query.
        """
        ask = AskQuery()
        qid = "http://purl.org/niquery/id/{0}".format(task_id)
        result = ask.describe_query(qid)
        return result.to_dict()


class Inference(Resource):
    def get(self):
        pass


class InferenceResult(Resource):
    def get(self, task_id):
        pass


class Compute(Resource):
    def get(self):
        select = SelectQuery(config=app.config)
        compute = select.sparql_meta.query_type == str(NS.niq.ComputeQuery)
        result = select.sparql_meta[compute]
        return result.to_dict(outtype='records')

    def post(self):
        args = parser.parse_args()
        result = []
        select = SelectQuery()
        df = select.execute_select(args['query_uuid'],
                                   turtle_str=args['turtle_file'])
        for record in df.to_dict(outtype='records'):
            task_id = record['task']
            task = celery.tasks[task_id]
            res = task.apply_async([record])
            record.update({"task_id": res.task_id})
            result.append(record)
        return result


class ComputeResult(Resource):
    def get(self, task_id):
        async = celery.AsyncResult(task_id)
        result = {'task_id': async.id,
                  'task_state': async.state}
        if async.ready():
            prov = async.get(timeout=1.0)
            graph = json.loads(prov['prov'])
            
            # connect to the configured store
            store = SelectQuery(config=app.config).get_graph().store
            sparql_store = rdflib.ConjunctiveGraph(store=store,
                                                   identifier=NS.iri[async.id])  
            
            # skolemize to handle bnodes and persist graph to sparqlstore
            g = rdflib.Graph()
            g.parse(data=prov['prov'], format='json-ld')
            g.skolemize(new_graph=sparql_store)

            # include named graph uri in response, and make json-ld compliant
            result.update({'graph_id': NS.iri[async.id],
                           '@graph': graph})
        return result

# Endpoints
api.add_resource(Validate, '/validate')
api.add_resource(ValidateResult, '/validate/<string:task_id>')
api.add_resource(Inference, '/inference')
api.add_resource(InferenceResult, '/inference/<string:task_id>')
api.add_resource(Compute, '/compute', '/compute/')
api.add_resource(ComputeResult, '/compute/<string:task_id>')

if __name__ == "__main__":

    app.run(host=app.config['HOST'], port=app.config['PORT'])

# TODO: 'Validate' NIDM API (Dataset Descriptor)
# TODO: Infer NIDM from XNAT + EXCEL (Experiment)
# TODO: Compute from NIDM (Workflow + Results)
