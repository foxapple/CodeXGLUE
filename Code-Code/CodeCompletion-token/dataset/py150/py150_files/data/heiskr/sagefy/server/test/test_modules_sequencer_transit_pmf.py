import pytest

xfail = pytest.mark.xfail


@xfail
def test_likelihood(app):
    """
    Expect to update the likelihood of a given hypothesis.
    """

    assert False


@xfail
def test_scale(app):
    """
    Expect to scale the output of the value.
    """

    assert False


"""
Expect to calculate transit.
Expect transit to increase with correct answer.
Expect transit to decrease with incorrect answer.
"""
