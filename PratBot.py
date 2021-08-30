"""
This is a template for Project 1, Task 1 (Induced demand-supply)

Developed by Prathyush Prashanth Rao - 1102225

----
TODO

# Define goals - it is the equation they gave
# Use print_trade_opportunity like a switch statement and use if statements in the super method to clarify reasoning

LEARNT
# received_holdings keeps upadating with every change in the market

"""

from asyncio import selector_events
from asyncio.windows_events import SelectorEventLoop
from enum import Enum
from fmclient import Agent, OrderSide, Order, OrderType, Session
from typing import List
import copy

from fmclient.data.orm.market import Market


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
        self._bot_type = BotType.REACTIVE          # Proactive vs reactive (Proactive default for now)
        self._pending_order = False                 # Execute only one order at a time
        self._wait_for_server = False               # Wait for server response before commiting to another order
        self._pending_private = False               # Once public market order is executed, follow-up with private execution
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
        self._incentive_load = False

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
        # Initial incentives loading - without which the code won't run
        if self._incentive_load:
            # Check if an order exists in the public market
            if not self._pending_order_check(orders):
                if not self._wait_for_server:
                    # Check if there has been a follow-up private market order
                    if not self._pending_private:
                        print("here 1")
                        # Then use different proactive/reactive stances
                        if self._bot_type == BotType.PROACTIVE:
                            self.proactive_bot()
                        else:
                            self.reactive_bot()
                    else:
                        self.send_private_order(self._incentive_side, self._incentive_price)
                        # Private order executed
                        self._pending_private = False
        
            # Check if incentives refreshed
            # print(" HEre -1")
            self.refresh_incentive()
            # Remove reactive bot order if it reacted too late
            for key, ord in Order.current().items():
                if ord.mine:
                    self.send_cancel_order(ord)
                    break
        else:
            self.initial_incentive()

    # To load all the initial incentives for the reactive/proactive bot to function
    def initial_incentive(self):
        # Initial incentive laod
        for key, ord in Order.current().items():
            if ord.mine:
                self.send_cancel_order(ord)
            elif ord.is_private:
                if ord.price != self._incentive_price or ord.order_side != self._incentive_side:
                    # self._incentive_changed = True
                    self._incentive_price = ord.price
                    self._incentive_side = ord.order_side
                    # print(f"Ord price and ord incentive is {ord.price} and {ord.order_side}")
                    self._incentive_load = True
                    break
            # No incentives found just yet (if entering in the middle of the session)
            print("No incentives yet")

    # Check if incentives have changed and refresh code accordingly
    def refresh_incentive(self):
        for key, ord in Order.current().items():
            if ord.is_private:
                # Incentives have changed
                if ord.price != self._incentive_price or ord.order_side != self._incentive_side:
                    self._incentive_changed = True
                    self._incentive_price = ord.price
                    self._incentive_side = ord.order_side
                    break
        if self._incentive_changed:
            # Cancel all my old orders, including old private orders
            self._incentive_changed = False
            for key, ord in Order.current().items():
                if ord.mine:
                    self.send_cancel_order(ord)

    def received_holdings(self, holdings):
        # Implement session change check, to reinitialize all boolean variables 
        if not (self._cash_initial == holdings.cash_initial):
            # Check for private and public initial widgets too
            # If check is true, cancel all previous orders and restart pending orders to false
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
        prv_exist = False
        for key, ord in Order.current().items():
            if ord.is_private:
                prv_exist = True
                break
        
        # If private orders do exist
        if prv_exist:
            # Check order here
            if self.order_check(self._incentive_side, self.proactive_price(self._incentive_side, self._incentive_price), False):
                # Test for public and that should automatically allow for private testing
                self.send_public_order(self._incentive_side, self.proactive_price(self._incentive_side, self._incentive_price))
                # print(f"Value we are going for is {self.proactive_price(self._incentive_side, self._incentive_price)} where prev_price is {self._incentive_price} and prev side is {self._incentive_side}")
                self._pending_private = True
                
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
        prv_exist = False
        # Bring buy down while bringing sell high using out of bound numbers
        # Find the highest buy to sell to, and the lowest sell to buy to long as they are profitable
        buy_high = -1
        sell_low = 11

        # Collect data to make reactive orders
        for key, ord in Order.current().items():
            if ord.is_private:
                prv_exist = True
            else:
                if ord.order_side == OrderSide.BUY:
                    if ord.price > buy_high:
                        buy_high = ord.price
                else: 
                    if ord.price < sell_low:
                        sell_low = ord.price
    
        if prv_exist:
            print("In prv reactive bot")
            trade_price = self.reactive_price(self._incentive_side, buy_high, sell_low, self._incentive_price)
            print(trade_price)
            if trade_price:
                # Create public market order
                self.send_public_order(self._incentive_side, trade_price)
                self._pending_private = True

    # A check function to see whether a valid price exists for the bot to react to
    def reactive_price(self, side, buy_high, sell_low, price):
        # Public market only
        if side == OrderSide.BUY:
            # No buy order exists
            if sell_low < price:
                if sell_low > self._cash_avail:
                    return sell_low
        else:
            print(f"buy high {buy_high}")
            if buy_high > price:
                if self._pub_widgets_avail > 0:
                    return buy_high
        # No profitable trade available
        return False

    # Function to check whether order can be possible or not
    def order_check(self, price, side, private = False):
        if private:
            # Manager wants to buy, which means the user will sell to react to the order
            if side == OrderSide.BUY:
                # Check if possible for the user (selling private widgets)
                if self._prv_widgets_avail > 0:
                    return True
                else:
                    return False
            else:
                if self._cash_avail >= price:
                    return True
                else:
                    return False
        else:
            # Here the user is buying orders from the public market (Therefore requires cash to buy)
            if side == OrderSide.BUY:
                if self._cash_avail >= price:
                    return True
                else:
                    return False
            else:
                if self._pub_widgets_avail > 0:
                    return True
                else:
                    return False

    # Function to send a specified order to the public market
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

    # Function to send a specified order to the private market
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

    # Cancel order if private order does not go through or incentives change
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
