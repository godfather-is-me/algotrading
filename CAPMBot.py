"""
This is a bot for the CAPM Task

Developed by Prathyush Prashanth Rao - 1102225

Subject code: FNCE30010
Student Number: 1102225
Name: Prathyush Prashanth Rao
Assignment: Task 2
"""
from typing import List
from fmclient import Agent, Session
from fmclient import Order, OrderSide, OrderType

import numpy as np
from itertools import combinations

# Submission details
SUBMISSION = {"student_number": "1102225", "name": "Prathyush Prashanth Rao"}

FM_ACCOUNT = "pollent-broker"
FM_EMAIL = "prathyushr@student.unimelb.edu.au"
FM_PASSWORD = "1102225"
MARKETPLACE_ID = 1309


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

        # Bot properties
        self._perfomance = 0            # Bot's performance with current stocks
        self._profit_margin = 0.25      # Profit margin for proactive bot
        self._avg_value = (1/4)         # Value used when required to average properties

    def initialised(self):
        # Extract payoff distribution for each security
        for _, market_info in self.markets.items():
            security = market_info.item
            description = market_info.description
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

        print(self._payoffs)
        self.inform("Bot initialised, I have the payoffs for the states.")

    def is_portfolio_optimal(self):
        """
        Returns true if the current holdings are optimal (as per the performance formula), false otherwise.
        :return:
        """
        pass
    
    # Function to get the performance of each possible trade
    def get_potential_performance(self, orders):
        
        pass

    # Function to update stocks and cash according to strategy and return it's perforance metric
    def _performance_update(self, stock_name, units):
        # To modify variables
        stocks_held = self._stocks_held.copy()
        cash = self._cash_avail
        reactive = True

        # Get current performance metric
        if not units:
            return self._expected_payoff(stocks_held, cash) - (self._risk_penalty * self._payoff_variance(stocks_held))

        # Buying units
        if units > 0:
            # If none, nothing to buy from sellers
            if self._curr_sell_prices[stock_name] is None:
                reactive = False

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

    def order_accepted(self, order):
        pass

    def order_rejected(self, info, order):
        pass

    def received_orders(self, orders: List[Order]):
        some_items = Order.current().items()
        # Dummy placeholder to ensure functioning
        self._current_market_values(some_items)


    # Function to find current market buy/sell prices
    def _current_market_values(self, items):
        # Refresh values to None if it does not exist
        self._refresh_values()
        for _, order in items:
            if order.order_side == OrderSide.BUY:
                if self._curr_buy_prices[order.market.item] is None:
                    self._curr_buy_prices[order.market.item] = order.price
                else:
                    self._curr_buy_prices[order.market.item] = max((order.price / 100), self._curr_buy_prices[order.market.item])
            else:
                if self._curr_sell_prices[order.market.item] is None:
                    self._curr_sell_prices[order.market.item] = order.price
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
