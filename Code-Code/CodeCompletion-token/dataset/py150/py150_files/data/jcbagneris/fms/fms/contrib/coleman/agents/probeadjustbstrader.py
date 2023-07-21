#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
Module defining ProbeAdjustBSTrader agent class.
"""
# Author: Patrick Coleman (Wharton Undergraduate 2012)

import random

from fms import agents
from fms.utils import BUY, SELL
from fms.utils.exceptions import MissingParameter

class ProbeAdjustBSTrader(agents.Agent):
    """
    Simulate an agent probing and adjusting
    with shared data for BUY, SELL orders

    This agent subclass should have two keys in the
    args dict :
    - maxprice : maximum order price (float)
    - maxbuy : maximum quantity to buy (int)
    If any of those parameters is missing, a MissingParameter
    exception is raised.
    >>> from fms.agents import zerointelligencetrader
    >>> params = {'agents': [{'money':10000, 'stocks':200}]}
    >>> agent = zerointelligencetrader.ZeroIntelligenceTrader(params)
    Traceback (most recent call last):
        ...
    MissingParameter: maxprice
    >>> params = {'agents': [{'money':10000, 'stocks':200, 'args':[999]}]}
    >>> agent = zerointelligencetrader.ZeroIntelligenceTrader(params)
    Traceback (most recent call last):
        ...
    MissingParameter: maxbuy
    >>> params = {'agents': [{'money':10000, 'stocks':200, 'args':[999, 100]}]}
    >>> agent = zerointelligencetrader.ZeroIntelligenceTrader(params)
    >>> print agent.state()
    Agent ... - owns $10000.00 and    200 securities
    >>> print agent.maxprice
    999
    >>> print agent.maxbuy
    100

    The ProbeAdjustBSTrader acts by returning a
    dict with (direction, price, quantity) keys.
    The 3 elements of the dict are randomly chosen,
    in uniform distributions based on the success 
    of previous buy or sell orders.
    >>> len(agent.act())
    3

    - direction is buy or sell
    - price is a %.2f float in [0.01,maxprice]
    - quantity is an int in :
      - if direction==BUY, [1,self.maxbuy]
      - if direction==SELL, [1,self.stocks]
    Thus, shortselling is not allowed.
    """
    
    def __init__(self, params, offset=0):
        agents.Agent.__init__(self, params, offset)
        try:
            self.maxprice = self.args[0]
        except (AttributeError, IndexError):
            raise MissingParameter, 'maxprice'
        try:
            self.maxbuy = self.args[1]
        except IndexError:
            raise MissingParameter, 'maxbuy'
        del self.args
        # {BUY: [prevprice, success], SELL: [prevprice, sucess]}
        self.prevorder = [self.maxprice/2., False]

    def act(self, world=None, market=None):
        """
        Return order as a dict with keys in (direction, price, quantity).
        If BUY, bid lower if last order was successful, otherwise higher.
        If SELL, bid higher if last order was successful, otherwise lower.
        Bids are random bounded by previous bid.

        To avoid short selling as far as possible, if # of stocks
        is zero or negative, force BUY direction.
          
        To avoid levering up as far as possible, if money
        is zero or negative, force SELL.
        """
        if self.stocks > 0 and self.money > 0:
            direction = random.choice((BUY, SELL))
        elif self.stocks <= 0:
            # Short selling is forbidden
            direction = BUY
        else:
            # money<=0, levering is discouraged
            direction = SELL
        if direction:
            if self.prevorder[1]:
                price = random.randint(int(self.prevorder[0]*100), \
                        self.maxprice*100)/100.
            else:
                price = random.randint(1, \
                        int(self.prevorder[0]*100))/100.
            quantity = random.randint(1, self.stocks)
        else:
            if self.prevorder[1]:
                price = random.randint(1, \
                        int(self.prevorder[0]*100))/100.
            else:
                price = random.randint(int(self.prevorder[0]*100), \
                        self.maxprice*100)/100.
            quantity = random.randint(1, self.maxbuy)
        self.prevorder = [price, False]
        return {'direction':direction, 'price':price, 'quantity':quantity}

    def record(self, direction, price, quantity):
        """
        Record transaction
        """
        if direction:
            self.stocks -= quantity
            self.money += quantity*price
        else:
            self.stocks += quantity
            self.money -= quantity*price
        self.prevorder = [price, True]


def _test():
    """
    Run tests in docstrings
    """
    import doctest
    doctest.testmod(optionflags=+doctest.ELLIPSIS)

if __name__ == '__main__':
    _test()
