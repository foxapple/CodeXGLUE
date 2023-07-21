from psycopg2 import IntegrityError
import random


class FailedToReserveUsername(Exception): pass
class RanOutOfUsernameAttempts(Exception): pass


def gen_random_usernames():
    """Yield random 12-hex-digit unicodes.
    """
    while 1:
        yield hex(int(random.random() * 16**12))[2:].zfill(12).decode('ASCII')


def insert_into_participants(cursor, username):
    return cursor.one( "INSERT INTO participants (username, username_lower) "
                       "VALUES (%s, %s) RETURNING username"
                     , (username, username.lower())
                      )


def safely_reserve_a_username(cursor, gen_usernames=gen_random_usernames,
                                                                 reserve=insert_into_participants):
    """Safely reserve a username.

    :param cursor: a :py:class:`psycopg2.cursor` managed as a :py:mod:`postgres`
        transaction
    :param gen_usernames: a generator of usernames to try
    :param reserve: a function that takes the cursor and does the SQL
        stuff
    :database: one ``INSERT`` on average
    :returns: a 12-hex-digit unicode
    :raises: :py:class:`FailedToReserveUsername` if no acceptable username is found
        within 100 attempts, or :py:class:`RanOutOfUsernameAttempts` if the username
        generator runs out first

    The returned value is guaranteed to have been reserved in the database.

    """
    cursor.execute("SAVEPOINT safely_reserve_a_username")

    seatbelt = 0
    for username in gen_usernames():
        seatbelt += 1
        if seatbelt > 100:
            raise FailedToReserveUsername

        try:
            check = reserve(cursor, username)
        except IntegrityError:  # Collision, try again with another value.
            cursor.execute("ROLLBACK TO safely_reserve_a_username")
            continue
        else:
            assert check == username
            break
    else:
        raise RanOutOfUsernameAttempts

    cursor.execute("RELEASE safely_reserve_a_username")
    return username
