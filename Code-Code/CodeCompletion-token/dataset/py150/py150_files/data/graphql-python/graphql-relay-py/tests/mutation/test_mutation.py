from collections import namedtuple
from pytest import raises
from graphql.core import graphql
from graphql.core.type import (
    GraphQLSchema,
    GraphQLObjectType,
    GraphQLInt,
    GraphQLField
)

from graphql_relay.mutation.mutation import (
    mutation_with_client_mutation_id,
)


class Result(object):

    def __init__(self, result, clientMutationId=None):
        self.clientMutationId = clientMutationId
        self.result = result

simpleMutation = mutation_with_client_mutation_id(
    'SimpleMutation',
    input_fields={},
    output_fields={
        'result': GraphQLField(GraphQLInt)
    },
    mutate_and_get_payload=lambda *_: Result(result=1)
)

mutation = GraphQLObjectType(
    'Mutation',
    fields={
        'simpleMutation': simpleMutation
    }
)

schema = GraphQLSchema(
    query=mutation,
    mutation=mutation
)


def test_requires_an_argument():
    query = '''
      mutation M {
        simpleMutation {
          result
        }
      }
    '''
    expected = {
        'allObjects': [
            {
                'id': 'VXNlcjox'
            },
            {
                'id': 'VXNlcjoy'
            },
            {
                'id': 'UGhvdG86MQ=='
            },
            {
                'id': 'UGhvdG86Mg=='
            },
        ]
    }
    result = graphql(schema, query)
    assert len(result.errors) == 1


def test_returns_the_same_client_mutation_id():
    query = '''
      mutation M {
        simpleMutation(input: {clientMutationId: "abc"}) {
          result
          clientMutationId
        }
      }
    '''
    expected = {
        'simpleMutation': {
            'result': 1,
            'clientMutationId': 'abc'
        }
    }
    result = graphql(schema, query)
    assert not result.errors
    assert result.data == expected


def test_contains_correct_input():
    query = '''
      {
        __type(name: "SimpleMutationInput") {
          name
          kind
          inputFields {
            name
            type {
              name
              kind
              ofType {
                name
                kind
              }
            }
          }
        }
      }
    '''
    expected = {
        '__type': {
            'name': 'SimpleMutationInput',
            'kind': 'INPUT_OBJECT',
            'inputFields': [
                {
                    'name': 'clientMutationId',
                    'type': {
                        'name': None,
                        'kind': 'NON_NULL',
                        'ofType': {
                            'name': 'String',
                            'kind': 'SCALAR'
                        }
                    }
                }
            ]
        }
    }
    result = graphql(schema, query)
    assert not result.errors
    assert result.data == expected


def test_contains_correct_payload():
    query = '''
      {
        __type(name: "SimpleMutationPayload") {
          name
          kind
          fields {
            name
            type {
              name
              kind
              ofType {
                name
                kind
              }
            }
          }
        }
      }
    '''
    expected1 = {
        '__type': {
            'name': 'SimpleMutationPayload',
            'kind': 'OBJECT',
            'fields': [
                {
                    'name': 'clientMutationId',
                    'type': {
                        'name': None,
                        'kind': 'NON_NULL',
                        'ofType': {
                            'name': 'String',
                            'kind': 'SCALAR'
                        }
                    }
                },
                {
                    'name': 'result',
                    'type': {
                        'name': 'Int',
                        'kind': 'SCALAR',
                        'ofType': None
                    }
                },
            ]
        }
    }
    expected2 = {
        '__type': {
            'name': 'SimpleMutationPayload',
            'kind': 'OBJECT',
            'fields': [
                {
                    'name': 'result',
                    'type': {
                        'name': 'Int',
                        'kind': 'SCALAR',
                        'ofType': None
                    }
                },
                {
                    'name': 'clientMutationId',
                    'type': {
                        'name': None,
                        'kind': 'NON_NULL',
                        'ofType': {
                            'name': 'String',
                            'kind': 'SCALAR'
                        }
                    }
                },
            ]
        }
    }
    result = graphql(schema, query)
    assert not result.errors
    assert result.data == expected1 or result.data == expected2


def test_contains_correct_field():
    query = '''
      {
        __schema {
          mutationType {
            fields {
              name
              args {
                name
                type {
                  name
                  kind
                  ofType {
                    name
                    kind
                  }
                }
              }
              type {
                name
                kind
              }
            }
          }
        }
      }
    '''

    expected = {
        '__schema': {
            'mutationType': {
                'fields': [
                    {
                        'name': 'simpleMutation',
                        'args': [
                            {
                                'name': 'input',
                                'type': {
                                    'name': None,
                                    'kind': 'NON_NULL',
                                    'ofType': {
                                        'name': 'SimpleMutationInput',
                                        'kind': 'INPUT_OBJECT'
                                    }
                                },
                            }
                        ],
                        'type': {
                            'name': 'SimpleMutationPayload',
                            'kind': 'OBJECT',
                        }
                    },
                ]
            }
        }
    }
    result = graphql(schema, query)
    assert not result.errors
    assert result.data == expected
