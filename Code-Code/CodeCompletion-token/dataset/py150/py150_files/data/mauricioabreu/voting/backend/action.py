from sqlalchemy.sql.expression import func

from backend.models import Option, Vote, Voting, VotingOption


def create_voting(data, session):
    """
    Create a Voting object.

    Args:
        description (str): Voting description.

    Returns:
        object: Voting object.
    """
    voting = Voting(description=data['description'])

    for option in data['options']:
        voting.options.append(Option(description=option['description']))

    session.add(voting)
    session.commit()

    return voting


def delete_voting(voting_id, session):
    """
    Delete a Voting object.

    Args:
        voting_id (int): Voting ID.
    """
    voting = session.query(Voting).get(voting_id)
    session.delete(voting)


def get_voting(voting_id, session):
    """
    Get a Voting object.

    Args:
        voting_id (int): Voting ID.
    Returns:
        object: Voting object.
    """
    return session.query(Voting).filter_by(id=voting_id).one()


def vote_for_option(option_id, session):
    """
    Vote for the given option.

    Args:
        option_id (int): Option ID.
    """
    vote = Vote(option_id=option_id)
    session.add(vote)
    session.commit()


def get_voting_result(voting_id, session):
    """
    Get result of a voting.

    Args:
        voting_id (int): Voting ID.
    """
    # TODO: How could this query-to-dict be better?
    queryset = session.query(VotingOption.option_id.label("option"), func.count(Vote.id).label("total_votes")).\
        filter(Voting.id == VotingOption.voting_id).\
        filter(VotingOption.id == Vote.option_id).\
        filter(Voting.id == voting_id).\
        group_by(Voting.id, VotingOption.id).all()
    result = []
    for row in queryset:
        result.append(dict(zip(row.keys(), row)))
    return result
