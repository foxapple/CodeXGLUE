from models.user import User
from framework.redis import redis
from modules.util import uniqid


def get_current_user(request):
    """
    Get the current user if available, else None.
    """

    cookies = request.get('cookies', {})
    session_id = cookies.get('session_id')
    user_id = redis.get(session_id)
    if user_id:
        user_id = user_id.decode()
        return User.get(request['db_conn'], id=user_id)


def log_in_user(user):
    """
    Log in the given user.
    """

    session_id = uniqid()
    redis.setex(
        session_id,
        2 * 7 * 24 * 60 * 60,
        user['id'],
    )
    return session_id


def log_out_user(request):
    """
    Log out the given user.
    """

    cookies = request.get('cookies', {})
    session_id = cookies.get('session_id')
    if session_id:
        redis.delete(session_id)
