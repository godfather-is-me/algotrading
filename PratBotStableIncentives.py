"""
This is a template for Project 1, Task 1 (Induced demand-supply)

Developed by Prathyush Prashanth Rao - 1102225

----
TODO

# Define goals - it is the equation they gave
#### Make send order function with buy/sell and price params
# Use print_trade_opportunity like a switch statement and use if statements in the super method to clarify reasoning

LEARNT
# received_holdings keeps upadating with every change in the market


Main local + super incentives, should be stable but check

"""

from asyncio import selector_events
from asyncio.windows_events import SelectorEventLoop
from enum import Enum
from fmclient import Agent, OrderSide, Order, OrderType, Session
from typing import List

from fmclient.data.orm.market import Market
import copy


# Student details
SUBMISSION = {"number": "1102225", "name": "Prathyush Prashanth Rao"}

# ------ Add a variable called PROFIT_MARGIN -----
PROFIT_MARGIN = 10
MIN_BUY = 0
MAX_SELL = 1000

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
        self._role = None                           # Buyer or seller from class
        self._bot_type = BotType.PROACTIVE          # Proactive vs reactive (Proactive default for now)
        self._pending_order = False                 # Execute only one order at a time
        self._wait_for_server = False               # Wait for server response before commiting to another order
        self._pending_private = False               # Once public market order is executed, follow-up with private execution
        self._pending_prv_side = None               # Private execution required info
        self._pending_prv_price = 0
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
        # Old incentives to compare when refreshed
        self._incentive_price = 0
        self._incentive_side = None
        self._incentive_changed = False

    def role(self):
        return self._role

    # Initialize the markets and other derived values from starting the server
    def initialised(self):
        # Set private and public market IDs
        for market_id, market in self.markets.items():
            if market.private_market:
                self._private_market_id = market_id
            else:
                self._public_market_id = market_id

    # Outcome message when order has been accepted into the market
    def order_accepted(self, order: Order):
        print(f"\nOrder ACCEPTED with the details - {order}")
        self._wait_for_server = False

    # Rejection message when order has failed to be accepted into the market
    def order_rejected(self, info, order: Order):
        print(f"\nOrder REJECTED with the details - {order} and info - {info}")
        self._wait_for_server = False

    # All trade opportunities seen before confirming the order
    def _print_trade_opportunity(self, other_order):
        self.inform(f"I am a {self.role()} with profitable order {other_order}")

    # Orders received by the server, holds order book
    def received_orders(self, orders: List[Order]):
        if not self._pending_order_check(orders):
            if not self._wait_for_server:
                if not self._pending_private:
                    # Then use different proactive/reactive stances
                    if self._bot_type == BotType.PROACTIVE:
                        self.proactive_bot()
                    else:
                        self.reactive_bot()
                else:
                    if self._bot_type == BotType.PROACTIVE:
                        self.send_private_order(self._pending_prv_side, self._pending_prv_price)
                        # Private order executed
                        self._pending_private = False
                    else:
                        pass
        # Check if incentives refreshed
        for key, ord in Order.current().items():
            if ord.is_private:
                # Incentives have changed
                if ord.price != self._incentive_price or ord.order_side != self._incentive_side:
                    self._incentive_changed = True
                    self
                    break
        if self._incentive_changed:
            # Cancel all my old orders
            self._incentive_changed = False
            for key, ord in Order.current().items():
                if ord.mine:
                    self.send_cancel_order(ord)

    def received_holdings(self, holdings):
        # Implement session change check, to reinitialize all boolean variables                             ------------
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

    # Returns boolean value if pending order exists (only 1 order at a time)
    def _pending_order_check(self, orders):
        for key, ord in Order.current().items():
            if ord.mine and ord.is_pending:
                return True
        return False

    # A proactive style bot that sends orders to bring liquidity into the market
    def proactive_bot(self):
        # Proactive bot to set itself based on the private market
        prv_price = 0
        prv_side = None
        prv_exist = False        #                                                     ------------- check!
        for key, ord in Order.current().items():
            if ord.is_private:
                prv_side = ord.order_side
                prv_price = ord.price
                prv_exist = True
        
        # If private orders do exist
        if prv_exist:
            # Check order here
            if self.order_check(prv_side, self.proactive_price(prv_side, prv_price), False):
                # Test for public and that should automatically allow for private testing
                self.send_public_order(prv_side, self.proactive_price(prv_side, prv_price))
                # print(f"Value we are going for is {self.proactive_price(prv_side, prv_price)} where prev_price is {prv_price} and prev side is {prv_side}")
                self._pending_private = True
                self._pending_prv_price = prv_price
                self._pending_prv_side = prv_side
                
    # If the private order is buy, buy lower in public. For sell, sell higher in public and buy private
    def proactive_price(self, side, price):
        if side == OrderSide.BUY:
            if ((price - PROFIT_MARGIN) >= MIN_BUY):
                return (price - PROFIT_MARGIN)
            else:
                return MIN_BUY
        else:
            if ((price + PROFIT_MARGIN) <= MAX_SELL):
                return (price + PROFIT_MARGIN)
            else:
                return MAX_SELL

    # A reactive style bot that sends orders based on the actions in the market
    def reactive_bot(self):
        pass

    # Function to check whether order can be possible or not
    def order_check(self, price, side, private = False):
        if private:
            # Manager wants to buy, which means the user will sell to react to the order
            if side == OrderSide.BUY:
                # Check if possible for the user (selling private widgets)
                if self._prv_widgets_avail >= 0:
                    return True
                else:
                    return False
            else:
                if (self._cash_avail - price) >= 0:
                    return True
                else:
                    return False
        else:
            # Here the user is buying orders from the public market (Therefore requires cash to buy)
            if side == OrderSide.BUY:
                if (self._cash_avail - price) >= 0:
                    return True
                else:
                    return False
            else:
                if self._pub_widgets_avail >= 0:
                    return True
                else:
                    return False

        pass

    def send_public_order(self, side, price):
        # Create a new order object
        new_order = Order.create_new()

        new_order.market = Market(self._public_market_id)
        new_order.price = price
        new_order.units = 1

        new_order.order_type = OrderType.LIMIT
        new_order.order_side = side
        new_order.ref = f"Public {side} for 1@{price}"
        self.send_order(new_order)
        # Only one order to be executed
        self._pending_order = True
        # Wait for server to respond
        self._wait_for_server = True

    def send_private_order(self, side, price):
        # Create a new order object
        new_order = Order.create_new()

        new_order.market = Market(self._private_market_id)
        new_order.price = price
        new_order.units = 1

        new_order.order_type = OrderType.LIMIT
        if side == OrderSide.BUY:
            new_order.order_side = OrderSide.SELL
        else:
            new_order.order_side = OrderSide.BUY

        new_order.ref = f"Private {side} for 1@{price}"
        # Send privately to manager
        new_order.owner_or_target = "M000"
        self.send_order(new_order)
        # Only one order to be executed at a time
        self._pending_order = True
        # Waiting for the server to repsond
        self._wait_for_server = True

    # Cancel order if private order does not go through
    # Cancel order if incentives change
    def send_cancel_order(self, order):
        cancel_order = copy.copy(order)
        cancel_order.order_type = OrderType.CANCEL
        cancel_order.ref = "Cancelled due to async or incentive change"
        self.send_order(cancel_order)

if __name__ == "__main__":
    FM_ACCOUNT = "pollent-broker"
    FM_EMAIL = "prathyushr@student.unimelb.edu.au"
    FM_PASSWORD = "1102225"
    MARKETPLACE_ID = 1301

    ds_bot = DSBot(FM_ACCOUNT, FM_EMAIL, FM_PASSWORD, MARKETPLACE_ID)
    ds_bot.run()
