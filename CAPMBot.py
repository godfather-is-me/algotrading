"""
This is a bot for the CAPM Task

Developed by Prathyush Prashanth Rao - 1102225

Subject code: FNCE30010
Student Number: 1102225
Name: Prathyush Prashanth Rao
Assignment: Task 2
"""

""" TO DO

# -- Take each stock name and check for performance with buy/sell
# -- If performance is better, add that to our list of stocks to execute
# -- List includes - [stock name, buy/sell, price, isReactive]
# Update list of all stocks currently being played with

# Is optimal portfolio needs to check is all values are 0 (no stocks neeeded to be traded)
# If false, go to send public order and create order management function to be called in received orders

# Then implement pedning order check for each stock
# Implement order accepted check, order rejected check
# Cancel orders for pending order if not isReactive has waited too long

"""
from enum import Enum
from typing import List
from fmclient import Agent, Session
from fmclient import Order, OrderSide, OrderType

import copy
import numpy as np
from itertools import combinations


# Submission details
SUBMISSION = {"student_number": "1102225", "name": "Prathyush Prashanth Rao"}

FM_ACCOUNT = "pollent-broker"
FM_EMAIL = "prathyushr@student.unimelb.edu.au"
FM_PASSWORD = "1102225"
MARKETPLACE_ID = 1309

LOWER_LIMIT = 3.0
UPPER_LIMIT = 7.0

class Strategy(Enum):
    REACTIVE = 0
    PROACTIVE = 1
    EMPTY_MARKET = 2


class CAPMBot(Agent):

    def __init__(self, account, email, password, marketplace_id, risk_penalty=0.001, session_time=20):
        """
        Constructor for the Bot
        :param account: Account name
        :param email: Email id
        :param password: password
        :param marketplace_id: id of the marketplace
        :param risk_penalty: Penalty for risk
        :param session_time: Total trading time for one session
        """
        super().__init__(account, email, password, marketplace_id, name="CAPM Bot")
        self._risk_penalty = risk_penalty
        self._session_time = session_time
        self._market_ids = {}

        # Payoff variables
        self._payoffs = {}
        self._payoffs_square = {}       # Squared payoffs
        self._payoffs_avg = {}          # Average of the states
        self._payoffs_var = {}          # Variance of the states
        self._payoffs_covar = {}        # Covariance of every 2 states

        # Market variables
        self._cash_avail = 0            # Cash available
        self._stocks_held = {}          # Stocks available
        self._curr_buy_prices = {}      # Current buy prices in the market
        self._curr_sell_prices = {}     # Current sell prices in the market
        self._curr_orders = {}          # Current orders in the market (stock_name: order, type, time)

        # Bot properties
        self._performance = 0            # Bot's performance with current stocks
        self._margin = 0.2              # Profit margin for proactive bot
        self._avg_value = (1/4)         # Value used when required to average properties

    def initialised(self):
        # Extract payoff distribution for each security
        for market_id, market_info in self.markets.items():
            security = market_info.item
            description = market_info.description
            self._market_ids[security] = market_id
            self._payoffs[security] = np.array([int(a) for a in description.split(",")]) / 100

        # Load payoff squares
        for key, value in self._payoffs.items():
            self._payoffs_square[key] = np.square(value)

        # Load payoff averages
        for key, value in self._payoffs.items():
            self._payoffs_avg[key] = np.average(value)

        # Load payoff variances
        for key, value in self._payoffs.items():
            self._payoffs_var[key] = np.average(self._payoffs_square[key]) - (self._payoffs_avg[key] ** 2)

        # Load payoff covariances
        for comb in combinations(self._payoffs.keys(), 2):
            state1 = self._payoffs[comb[0]]
            state2 = self._payoffs[comb[1]]
            self._payoffs_covar[comb] = (np.dot(state1, state2) * self._avg_value) - (self._payoffs_avg[comb[0]] * self._payoffs_avg[comb[1]])

        # Load current orders in market (No orders when initialized)
        for key in self._payoffs.keys():
            self._curr_orders[key] = None

        print(self._payoffs)
        self.inform("Bot initialised, I have the payoffs for the states.")
    
    # Function to get the performance of all stocks and return orders (empty or full)
    def is_portfolio_optimal(self):
        # Check for every market
        stock_name = ''
        units = 0
        to_order = {}   # Orders to be executed

        # Initial performance
        self._performance = self.get_potential_performance(stock_name, units)[0]

        # Check all stocks
        for key in self._stocks_held.keys():
            # Set up order dictionary
            to_order[key] = None

            buy_performance, buy_price, buy_strategy = self.get_potential_performance(key, 1)
            sell_performance, sell_price, sell_strategy = self.get_potential_performance(key, -1)
            if buy_performance > sell_performance:
                if buy_performance > self._performance:
                    to_order[key] = [key, 1, round(buy_price, 3), buy_strategy]
            else:
                if sell_performance > self._performance:
                    to_order[key] = [key, -1, round(sell_price, 3), sell_strategy]
                
        return to_order
                
    # Function to get the potential performance of each stock and return metric
    def get_potential_performance(self, stock_name, units):
        # To modify variables
        stocks_held = self._stocks_held.copy()
        inital_cash = self._cash_avail
        cash = self._cash_avail
        strategy = Strategy.REACTIVE
        return_val = []                     # Return [performance, price]

        # Get current performance metric
        if not units:
            return [self._expected_payoff(stocks_held, cash) - (self._risk_penalty * self._payoff_variance(stocks_held)), 0]
        
        # Buying units
        if units > 0:
            # If none, nothing to buy from sellers
            if self._curr_sell_prices[stock_name] is None:
                strategy = Strategy.PROACTIVE
                if self._curr_buy_prices[stock_name] is None:
                    # Nothing in the market, create optimal price               # -------- tangent price
                    strategy = Strategy.EMPTY_MARKET
            # Check if cash is available
            if not self._cash_check(stock_name, strategy):
                return [0, 0]
            stocks_held[stock_name] += units
            if strategy == Strategy.REACTIVE:
                cash -= self._curr_sell_prices[stock_name]
            elif strategy == Strategy.PROACTIVE:
                cash -= (self._curr_buy_prices[stock_name] + self._margin)
            else:
                cash -= LOWER_LIMIT
        else:
            if self._curr_buy_prices[stock_name] is None:
                strategy = Strategy.PROACTIVE
                if self._curr_sell_prices[stock_name] is None:
                    # Nothing in the market, create optimal price using tangency
                    strategy = Strategy.EMPTY_MARKET
            # Check if stock is available
            if not self._unit_check(stock_name):
                return [0, 0]
            stocks_held[stock_name] += units
            if strategy == Strategy.REACTIVE:
                cash += self._curr_buy_prices[stock_name]
            elif strategy == Strategy.PROACTIVE:
                cash += (self._curr_sell_prices - self._margin)
            else:
                cash += UPPER_LIMIT

        # Return values
        return_val.append(self._expected_payoff(stocks_held, cash) - (self._risk_penalty * self._payoff_variance(stocks_held)))
        return return_val + [abs(inital_cash - cash)] + [strategy]
    
    # Safety function to check if cash available to buy
    def _cash_check(self, stock_name, strat):
        if strat == Strategy.REACTIVE:
            return (self._cash_avail - self._curr_sell_prices[stock_name]) >= 0
        elif strat == Strategy.PROACTIVE:
            return (self._cash_avail - (self._curr_buy_prices[stock_name] + self._margin)) >= 0
        # else
        return (self._cash_avail - LOWER_LIMIT)

    # Safety function to check if stock available to sell
    def _unit_check(self, stock_name):
        return self._stocks_held[stock_name] > 0

    # Function to calculate expected payoff from excel sheet
    def _expected_payoff(self, stocks_held, cash):
        payoff_sum = 0
        for key, value in stocks_held.items():
            payoff_sum += (self._payoffs_avg[key] * value)
        return (payoff_sum + cash)

    # Function to calculate payoff variance from excel
    def _payoff_variance(self, stocks_held):
        payoff_sum = 0
        for key, value in stocks_held.items():
            payoff_sum += ((value ** 2) * self._payoffs_var[key])
        for key, value in self._payoffs_covar.items():
            payoff_sum += 2 * value * stocks_held[key[0]] * stocks_held[key[1]]
        return payoff_sum

    # Function to manage orders
    # i.e. to cancel and create orders when required
    # Receives orders from is_optimal 
    # Excutes if not already in place, if in place do nothing
    # Cancel orders that were supposed to be reactive
    # Proacitve orders have a timer on them
    # Is empty orders are cancelled when market is not empty anymore
    def order_manager(self, market_orders):
        # Get all orders, if none market is optimal with the stock
        to_order = self.is_portfolio_optimal()

        # ---- Function to cancel reactive orders not executed, proactive orders after 30 seconds, or non-empty markets

        for key, value in to_order.items():
            # Current performance for the stock is optimal, or order exists
            if (value is None) or not (self._curr_orders[key] is None):
                continue

    # Function to create order
    def _create_order(self, stock_name, side, price, strategy):
        new_order = Order.create_new()
        new_order.market = self._market_ids[stock_name]
        new_order.order_side = side
        new_order.price = price
        new_order.order_type = OrderType.LIMIT
        new_order.ref = str(strategy)
        self.send_order(new_order)
        # Return order so it can be cancelled if need be
        return new_order

    # Function to cancel order
    def _cancel_order(self, order):
        cancel_order = copy.copy(order)
        cancel_order.order_type = OrderType.CANCEL
        cancel_order.ref = "Cancelled due to strategy"
        self.send_order(cancel_order)

    # Function to cancel orders as per strategy
    def _cancel_order_strategy(self, market_orders):
        # Uses self._curr_orders
        # Clear if order does not exist
        # Cancel reactive straight up if still available
        # Cancel proactive after 1 minute of no activity
        # Cancel empty market if other orders are seen

        for key, value in self._curr_orders.items():
            # Current order does not exist
            if value is None:
                continue

            # Curr order value in the format [order, strategy, time]


    def order_accepted(self, order):
        pass

    def order_rejected(self, info, order):
        pass

    def received_orders(self, orders: List[Order]):
        some_items = Order.current().items()
        # Dummy placeholder to ensure functioning
        self._current_market_values(some_items)

        self.is_portfolio_optimal()

    # Function to find current market buy/sell prices
    def _current_market_values(self, items):
        # Refresh values to None if it does not exist
        self._refresh_values()
        for _, order in items:
            if not order.mine:
                if order.order_side == OrderSide.BUY:
                    if self._curr_buy_prices[order.market.item] is None:
                        self._curr_buy_prices[order.market.item] = order.price / 100
                    else:
                        self._curr_buy_prices[order.market.item] = max((order.price / 100), self._curr_buy_prices[order.market.item])
                else:
                    if self._curr_sell_prices[order.market.item] is None:
                        self._curr_sell_prices[order.market.item] = order.price / 100
                    else:
                        self._curr_sell_prices[order.market.item] = min((order.price / 100), self._curr_sell_prices[order.market.item])

    # Function to refresh values to
    def _refresh_values(self):
        for key in self._stocks_held.keys():
            self._curr_buy_prices[key] = None
            self._curr_sell_prices[key] = None
        # self._curr_sell_prices['note'] = 5.0

    def received_session_info(self, session: Session):
        pass

    def pre_start_tasks(self):
        pass
    
    # Function to log stocks and cash currently owned
    def received_holdings(self, holdings):
        # Store cash and stocks
        self._cash_avail = holdings.cash_available / 100
        for market, asset in holdings.assets.items():
            self._stocks_held[market.item] = asset.units_available

        # Print values
        print(f"Cash settled - {holdings.cash} and cash available 0 {holdings.cash_available}")
        for market, asset in holdings.assets.items():
            print(f"Assets settled {asset.units} and available {asset.units_available} for market {market.item}")


if __name__ == "__main__":
    bot = CAPMBot(FM_ACCOUNT, FM_EMAIL, FM_PASSWORD, MARKETPLACE_ID)
    bot.run()
