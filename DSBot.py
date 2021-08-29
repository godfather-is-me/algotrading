"""
This is a template for Project 1, Task 1 (Induced demand-supply)

Developed by Prathyush Prashanth Rao - 1102225
"""

from enum import Enum
from fmclient import Agent, OrderSide, Order, OrderType, Session
from typing import List

# Student details
SUBMISSION = {"number": "1102225", "name": "Prathyush Prashanth Rao"}

# ------ Add a variable called PROFIT_MARGIN -----
PROFIT_MARGIN = 10


# Enum for the roles of the bot
class Role(Enum):
    BUYER = 0
    SELLER = 1


# Let us define another enumeration to deal with the type of bot
class BotType(Enum):
    PROACTIVE = 0
    REACTIVE = 1


class DSBot(Agent):
    # ------ Add an extra argument bot_type to the constructor -----
    def __init__(self, account, email, password, marketplace_id):
        super().__init__(account, email, password, marketplace_id, name="PratBot")
        self._public_market_id = 0
        self._private_market_id = 0
        self._role = None           # Buyer or seller ###
        self._bot_type = None       # Proactive vs reactive ###
        self._order_sent = False    # Execute only one order at a time
        # Set intial cash, cash available, assets, assets available for both private and public

        # ------ Add new class variable _bot_type to store the type of the bot

    def role(self):
        return self._role

    def initialised(self):
        # Set private and public market IDs
        for market_id, market in self.markets.items():
            if market.private_market:
                self._private_market_id = market_id
            else:
                self._public_market_id = market_id

    def order_accepted(self, order: Order):
        print(f"My order was accepted and the details are {order}")

    def order_rejected(self, info, order: Order):
        print(f"My order was rejected and the details of the order {order} are {info}")

    def received_orders(self, orders: List[Order]):
        print("Current order book is given by")
        #Order.current = classmethod(Order.current)
        #for i, ord in Order.current():
        #    print(ord)
        for o in orders:
            print(o)

    def _print_trade_opportunity(self, other_order):
        self.inform(f"I am a {self.role()} with profitable order {other_order}")

    def received_holdings(self, holdings):
        print(f"I have holding cash {holdings.cash} and cash available {holdings.cash_available}")
        print("\nAlso\n")
        for market, asset in holdings.assets.items():
            print(f"Assets settled {asset.units} and available {asset.units_available} for market {market}")

    def received_session_info(self, session: Session):
        pass

    def pre_start_tasks(self):
        pass


if __name__ == "__main__":
    FM_ACCOUNT = "pollent-broker"
    FM_EMAIL = "prathyushr@student.unimelb.edu.au"
    FM_PASSWORD = "1102225"
    MARKETPLACE_ID = 1301

    ds_bot = DSBot(FM_ACCOUNT, FM_EMAIL, FM_PASSWORD, MARKETPLACE_ID)
    ds_bot.run()
