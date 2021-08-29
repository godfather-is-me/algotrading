"""
This is a template for Project 1, Task 1 (Induced demand-supply)

Developed by Prathyush Prashanth Rao - 1102225
"""

from enum import Enum
from fmclient import Agent, OrderSide, Order, OrderType, Session
from typing import List

from fmclient.data.orm.market import Market

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

    # Sets all initial derived values
    def initialised(self):
        # Set private and public market IDs
        for market_id, market in self.markets.items():
            if market.private_market:
                self._private_market_id = market_id
            else:
                self._public_market_id = market_id

    # Function that returns approval when order accepted into order book
    def order_accepted(self, order: Order):
        print(f"My order was accepted and the details are {order}")

    # Function that return error when order rejected from order book
    def order_rejected(self, info, order: Order):
        print(f"My order was rejected and the details of the order {order} are {info}")

    def _print_trade_opportunity(self, other_order):
        self.inform(f"I am a {self.role()} with profitable order {other_order}")

    """ Trying to send orders as a test"""
    def received_orders(self, orders: List[Order]):
        # Going through the list of orders
        for ord in orders:
            if not self._order_sent:
                new_order = Order.create_new()
                new_order.market = Market(self._public_market_id)
                new_order.price = 500
                new_order.units = 1
                new_order.order_type = OrderType.LIMIT
                new_order.order_side = OrderSide.SELL
                new_order.ref = "test order"
                self.send_order(new_order)
                # Check to not break
                self._order_sent = True
        # This is a continuous loop, use it as outermost when making decisions?
        # Check async lecture
        print("\nThese are your current orders")
        for key, val in Order.current().items():
            print(val)
        """
        Example output
        These are your current orders
        Order(20392435,Others,BUY,5@680,private widget,LIMIT,REF:'T043',PVT_FROM:M000)
        Order(20392480,Others,SELL,1@690,widget,LIMIT,REF:'1 OrderSide.SELL order in Market(2279,widget,Widget,False)')
        Order(20392481,Others,BUY,1@60,widget,LIMIT)
        Order(20392599,Others,BUY,1@305,widget,LIMIT,REF:'buy-order')
        Order(20392629,Others,SELL,3@850,widget,LIMIT)
        """
        print("\nThis is your last traded?")    # Yes
        print(Order.trades()[0])


    def received_holdings(self, holdings):
        print(f"I have holding cash {holdings.cash} and cash available {holdings.cash_available}")
        print("Also")
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
