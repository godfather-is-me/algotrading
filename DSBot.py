"""
This is a template for Project 1, Task 1 (Induced demand-supply)

Developed by Prathyush Prashanth Rao - 1102225
"""

from asyncio import selector_events
from asyncio.windows_events import SelectorEventLoop
from enum import Enum
from fmclient import Agent, OrderSide, Order, OrderType, Session
from typing import List

from fmclient.data.orm.market import Market

# Student details
SUBMISSION = {"number": "1102225", "name": "Prathyush Prashanth Rao"}

# ------ Add a variable called PROFIT_MARGIN -----
PROFIT_MARGIN = 10
MIN_BUY = 0
MAX_SELL = 1000

# Define goals - it is the equation they gave

# Checks for whether there are holdlings available in the private and public market before making and buy or sell order
# Try using the last executed price to make your strategy

# The need for current orders is still vague. (One thing used is to check whether your order is in the system or not)
    # If possible, understand the minimum selling price, maximum buying price and if opportunity exists within both execute at that point, else just place order and wait for reaction

# --- learnt
# received_holdings keeps upadating with every change in the market

# Make send order function with buy/sell and price params

# Use print_trade_opportunity like a switch statement and use if statements in the super method to clarify reasoning

# --- Extra
# React to changes from the manager - store the previous state and if change remove current orders in the public market

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
        self._role = None               # Buyer or seller
        self._bot_type = None           # Proactive vs reactive
        self._pending_order = False    # Execute only one order at a time
        self._wait_for_server = False
        self._wait_for_public = False
        ## Restrictive check vars
        # Set intial cash and widgets for both public and private markets
        self._cash_initial = None
        self._pub_widgets_initial = None
        self._prv_widgets_initial = None
        # Assets and cash - settled and available
        self._cash_settled = None
        self._cash_avail = None
        self._pub_widgets_settled = None
        self._pub_widgets_avail = None
        self._prv_widgets_settled = None
        self._prv_widgets_avail = None


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
        self._wait_for_server = False

    # Function that return error when order rejected from order book
    def order_rejected(self, info, order: Order):
        print(f"My order was rejected and the details of the order {order} are {info}")
        self._wait_for_server = False

    # Function that shows various trade opportunities available
    def _print_trade_opportunity(self, other_order):
        self.inform(f"I am a {self.role()} with profitable order {other_order}")

    # Returns boolean if pending order exists
    def _pending_order_check(self, orders):
        for key, ord in Order.current().items():                                    # ------------------------- Check !!!
            if ord.mine and ord.is_pending:
                return True
        return False

    # Function called with changing orders, allows us to understand the market and make informed decisions
    def received_orders(self, orders: List[Order]):
        # Check if order exists in the public market
        self._pending_order = self._pending_order_check(orders)

        if not self._pending_order:
            # Check if you are not waiting for pending action from the server
            if not self._wait_for_server:
                self.proactive()

    # A proactive bot call function
    def proactive(self):
        # print proactive logic
        # Store current incentive
        prv_price = 0
        #best_sell = MAX_SELL
        #best_buy = MIN_BUY
        for key, ord in Order.current().items():
            if ord.is_private and ord.is_pending:
                self._role = ord.order_side
                prv_price = ord.price
        
        # Take one price and one type
        self.send_public_order(prv_price)
        


    def reactive(self):
        pass

    def send_private_order(self, price):
        new_order = Order.create_new()

        new_order.market = Market(self._private_market_id)
        new_order.price = price
        new_order.units = 1

        new_order.order_type = OrderType.LIMIT
        if self._role == OrderSide.BUY:
            new_order.order_side = OrderSide.SELL
        else:
            new_order.order_side = OrderSide.BUY
        new_order.ref = f"Private {self._role} for 1@{price}"
        self.owner_or_target = "M000"
        self.send_order(new_order)
        # Check to not break
        self._pending_order = True
        self._wait_for_server = True

    # Sends an order with specifications
    def send_public_order(self, price):
        # Create a new order 
        new_order = Order.create_new()

        new_order.market = Market(self._public_market_id)
        new_order.price = price
        new_order.units = 1

        new_order.order_type = OrderType.LIMIT
        new_order.order_side = self._role
        new_order.ref = f"Public {self._role} for 1@{price}"
        self.send_order(new_order)
        # Check to not break
        self._pending_order = True
        self._wait_for_server = True

        # This is a continuous loop, use it as outermost when making decisions?
        # Check async lecture
        #print("\nThese are your current orders")
        #for key, val in Order.current().items():
        #    print(val)
        """
        Example output
        These are your current orders
        Order(20392435,Others,BUY,5@680,private widget,LIMIT,REF:'T043',PVT_FROM:M000)
        Order(20392480,Others,SELL,1@690,widget,LIMIT,REF:'1 OrderSide.SELL order in Market(2279,widget,Widget,False)')
        Order(20392481,Others,BUY,1@60,widget,LIMIT)
        Order(20392599,Others,BUY,1@305,widget,LIMIT,REF:'buy-order')
        Order(20392629,Others,SELL,3@850,widget,LIMIT)
        """
        #print("\nThis is your last traded?")    # Yes
        #print(Order.trades()[0])

    def received_holdings(self, holdings):

        # Implement difference check here
        if not (self._cash_initial == holdings.cash_initial):
            # Check for private and public initial widgets too
            # If check is true, restart pending orders to false
            # Cancel all previous orders
            pass

        # Set cash
        self._cash_initial = holdings.cash_initial
        self._cash_avail = holdings.cash_available
        self._cash_settled = holdings.cash

        # Set widgets
        for market, asset in holdings.assets.items():
            if market.private_market:
                self._prv_widgets_initial = asset.units_initial
                self._prv_widgets_avail = asset.units_available
                self._prv_widgets_settled = asset.units
            else:
                self._pub_widgets_initial = asset.units_initial
                self._pub_widgets_avail = asset.units_available
                self._pub_widgets_settled = asset.units

        print(f"I have holding cash {holdings.cash} and cash available {holdings.cash_available}")
        # print("Also")
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
