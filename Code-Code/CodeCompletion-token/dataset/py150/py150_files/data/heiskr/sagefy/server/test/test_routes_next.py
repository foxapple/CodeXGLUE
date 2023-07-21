import routes.next
from models.user import User


def test_seq_next(db_conn, session):
    """
    Expect sequencer route to say where to go next.
    """

    request = {
        'cookies': {'session_id': session},
        'db_conn': db_conn,
    }
    user = User.get(db_conn, id='abcd1234')
    user.set_learning_context(next={
        'method': 'DANCE',
        'path': '/s/unicorns'
    })
    code, response = routes.next.next_route(request)
    assert code == 200
    assert response['next']['method'] == 'DANCE'
    user.set_learning_context(next=None)


def test_seq_next_default(db_conn, session):
    """
    Expect sequencer route to say where to go next if no current state.
    """

    request = {
        'cookies': {'session_id': session},
        'db_conn': db_conn,
    }
    code, response = routes.next.next_route(request)
    assert code == 200
    assert response == {
        'next': {
            'method': 'GET',
            'path': '/s/users/abcd1234/sets',
        }
    }
