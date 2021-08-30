"""
This is a template for Project 1, Task 1 (Induced demand-supply)

Developed by Prathyush Prashanth Rao - 1102225

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

# PROFIT_MARGIN initialised
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
    def __init__(self, account, email, password, marketplace_id, bot_type):
        super().__init__(account, email, password, marketplace_id, name="PratBot")
        self._public_market_id = 0
        self._private_market_id = 0
        self._role = None                           # Buyer or seller from class
        self._bot_type = bot_type                   # Proactive vs reactive (Proactive default)
        self._pending_order = False                 # Execute only one order at a time
        self._wait_for_server = False               # Wait for server response before commiting to another order
        self._pending_private = False               # Once public market order is executed, follow-up with private execution
        ## Restrictive checks
        # Assets and cash - settled and available
        self._cash_avail = None                     # All resources currently available
        self._pub_widgets_avail = None
        self._prv_widgets_avail = None
        # Old incentives to compare when refreshed
        self._incentive_price = 0                   # Incentive information available to the class
        self._incentive_side = None
        self._incentive_changed = False
        self._incentive_load = False
        # Collects a list of opportunities that could be analyzed
        self._opportunity = {}

    def role(self):
        return self._role

    # Initialize the markets when starting the server
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

    # Orders received by the server, holds the order book
    def received_orders(self, orders: List[Order]):
        # Initial incentives loading - with which the strategy is dependant on
        if self._incentive_load:
            # Check if an order has been sent to the public market
            if not self._pending_order_check(orders):
                # Wait for server to respond
                if not self._wait_for_server:
                    # Check if there has been a follow-up private market order
                    if not self._pending_private:
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
            self.refresh_incentive()
            # Remove reactive bot order if it reacted too late
            if self._bot_type == BotType.REACTIVE:
                for key, ord in Order.current().items():
                    if ord.mine and ord.is_pending:
                        self.send_cancel_order(ord)
                        break
        else:
            self.initial_incentive()

    # To load all the initial incentives for the reactive/proactive bot to function
    def initial_incentive(self):
        # Initial incentive laod
        for key, ord in Order.current().items():
            if ord.mine and ord.is_pending:
                self.send_cancel_order(ord)
            elif ord.is_private:
                # Different starting incentives
                if ord.price != self._incentive_price or ord.order_side != self._incentive_side:
                    self._incentive_price = ord.price
                    self._incentive_side = ord.order_side
                    self._incentive_load = True
                    # Update role of the bot according to incentive
                    if ord.order_side == OrderSide.BUY:
                        self._role = Role.BUYER
                    else:
                        self.role = Role.SELLER
                    break
            # No incentives found just yet (if entering in the middle of the session)
            # print("No incentives yet")

    # Check if incentives have changed and refresh orders accordingly
    def refresh_incentive(self):
        for key, ord in Order.current().items():
            if ord.is_private:
                # IF incentives have changed
                if ord.price != self._incentive_price or ord.order_side != self._incentive_side:
                    self._incentive_changed = True
                    self._incentive_price = ord.price
                    self._incentive_side = ord.order_side
                    # Update role of the bot according to incentive
                    if ord.order_side == OrderSide.BUY:
                        self._role = Role.BUYER
                    else:
                        self.role = Role.SELLER
                    break
        
        if self._incentive_changed:
            # Cancel all my old orders, including old private orders
            for key, ord in Order.current().items():
                if ord.mine and ord.is_pending:
                    self.send_cancel_order(ord)
            self._incentive_changed = False

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
                #self._print_trade_opportunity(ord)
                break
        
        # If private orders do exist
        if prv_exist:
            # Check order here
            if self.order_check(self._incentive_side, self.proactive_price(self._incentive_side, self._incentive_price)):
                # Order check not necessary for the private market as a successful public market order holds all that is required
                self.send_public_order(self._incentive_side, self.proactive_price(self._incentive_side, self._incentive_price))
                # Next step is the private market order
                self._pending_private = True
                
    # Private buy order, aim to buy lower in the public market. For sell orders, aim higher.
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
        # Working the opposite way to get the best buy to sell to and the best sell to buy
        buy_high = -1
        sell_low = 11

        # Collect data to make reactive orders
        for __, ord in Order.current().items():
            if ord.is_private:
                prv_exist = True
                self._opportunity['private'] = ord
            else:
                if ord.order_side == OrderSide.BUY:
                    if ord.price > buy_high:
                        buy_high = ord.price
                        self._opportunity[ord.price] = ord
                else: 
                    if ord.price < sell_low:
                        sell_low = ord.price
                        self._opportunity[ord.price] = ord
        
        # If a private order exists
        if prv_exist:
            trade_price = self.reactive_price(self._incentive_side, buy_high, sell_low, self._incentive_price)
            if trade_price:
                # Create public market order
                self.send_public_order(self._incentive_side, trade_price)
                self._pending_private = True
                self._opportunity['trade_price'] = trade_price
                
                # To reduce hinderance with the reactive bot and increase it's speed, all trades were stored and explained later
                # self._print_trade_opportunity()

    # A check function to see whether a valid price exists for the bot to react to
    def reactive_price(self, side, buy_high, sell_low, price):
        # Public market only
        if side == OrderSide.BUY:
            # No buy order exists
            if (sell_low + PROFIT_MARGIN) < price:
                if sell_low > self._cash_avail:
                    return (sell_low + PROFIT_MARGIN)
        else:
            if (buy_high + PROFIT_MARGIN) > price:
                if self._pub_widgets_avail > 0:
                    return (buy_high + PROFIT_MARGIN)
        # No profitable trade available
        return False

    # Function to check whether order can be possible or not
    def order_check(self, price, side):
        # Here the user is buying orders from the public market (Therefore requires cash to buy)
        if side == OrderSide.BUY:
            if self._cash_avail >= price:
                return True
            else:
                return False
        else:
            # Check for sell orders
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

    # Function to send a cancel order in either public or private markets
    def send_cancel_order(self, order):
        cancel_order = copy.copy(order)
        cancel_order.order_type = OrderType.CANCEL
        cancel_order.ref = "Cancelled due to async or incentive change"
        self.send_order(cancel_order)

    # All trade opportunities available before confirming the order
    def _print_trade_opportunity(self):
        # Initial
        available_cash = self._cash_avail

        # If the trade has already happened
        if 'trade_price' in self._oppportunity.keys():
            available_cash += self._oppportunity['trade_price']
        if 'private' in self._oppportunity.keys():
            print(f"I am a {self.role()} driven by the private incentive {self._oppportunity['private']}")
        
        # Check constraints and availability
        def check_constraints(order):
            if order.order_side == OrderSide.BUY:
                if order.price > available_cash:
                    return False
            else:
                if self._pub_widgets_avail <= 0:
                    return False
            return True

        # Check profitability
        def profitability(order):
            # If > 0, profitable
            return  order.price - self._oppportunity['private'].price

        # For all reactive bots that were possible
        for key, value in self._oppportunity.items():
            # Skip private key
            if key == 'private' or key == 'trade_place':
                continue
            if check_constraints(value):
                # It did not get executed because it was not the best bid/ask
                print(f"The {self.role()} order with {value} was a possible outcome with a profitability of {profitability(value)}")
            else:
                print(f"The {self.role()} order with {value} did not have sufficient resources")
        
        # Best bid/ask
        if self._oppportunity['trade_price']:
            print(f"The best {self._incentive_side} traded at {self._oppportunity['trade_price']}")

    # Holds all the current values of available holdings i.e. cash/widgets
    def received_holdings(self, holdings):
        # Set cash
        self._cash_avail = holdings.cash_available

        # Set widgets
        for market, asset in holdings.assets.items():
            if market.private_market:
                self._prv_widgets_avail = asset.units_available
            else:
                self._pub_widgets_avail = asset.units_available

        # Up=to-date about the current portfolio
        print(f"I have holding cash {holdings.cash} and cash available {holdings.cash_available}")
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
    BOT_TYPE = BotType.REACTIVE

    ds_bot = DSBot(FM_ACCOUNT, FM_EMAIL, FM_PASSWORD, MARKETPLACE_ID, BOT_TYPE)
    ds_bot.run()
