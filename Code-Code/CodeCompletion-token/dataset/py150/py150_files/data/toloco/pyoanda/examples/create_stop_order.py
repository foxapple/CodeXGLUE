"""How to create a stop order without pulling out all your hair :-)
"""
import datetime

from pyoanda import Client, PRACTICE, Order

client = Client(
    environment=PRACTICE,
    account_id="{{ACCOUNT_ID}}",
    access_token="{{ACCOUNT_TOKEN}}"
)

test_order = Order(
    instrument="EUR_JPY",
    units=10,
    side="buy",
    type="stop",
    stopLoss=80.95,
    takeProfit=170.56,
    price=10.0,
    expiry=datetime.datetime.now() + datetime.timedelta(days=1)
)

stop_order = client.create_order(order=test_order)
