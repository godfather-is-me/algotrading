"""
This is a template bot for  the CAPM Task.

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
MARKETPLACE_ID = 1309  # replace this with the marketplace id


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
        self._payoffs = {}
        self._payoffs_square = {}
        self._payoffs_var = {}
        self._payoffs_covar = {}

        self._risk_penalty = risk_penalty
        self._session_time = session_time
        self._market_ids = {}

        # Initiate base values for formula
        self._cash_avail = None
        self._current_stocks = {}
        self._current_buy = {}
        self._current_sell = {}

        # Bot properties
        self._reactive = True
        self._performace = 0
        self._profit_margin = 0.25
        self._avg_len_div = (1 / 4)               # To average values

    def initialised(self):
        # Extract payoff distribution for each security
        for _, market_info in self.markets.items():
            security = market_info.item
            description = market_info.description
            self._payoffs[security] = np.array([int(a) for a in description.split(",")]) / 100

        # Load payoff squares
        for key, value in self._payoffs.items():
            self._payoffs_square[key] = np.square(value)

        # Load variances
        for key, value in self._payoffs.items():
            self._payoffs_var[key] = (self._avg_len_div * np.sum(self._payoffs_square[key])) - ((self._avg_len_div * np.sum(value)) ** 2)

        # Load covariances
        for i in combinations(self._payoffs.keys(), 2):
            payoff1 = self._payoffs[i[0]]
            payoff2 = self._payoffs[i[1]]
            self._payoffs_covar[i] = (np.dot(payoff1, payoff2) * self._avg_len_div) - (np.average(payoff1) * np.average(payoff2))

        print(self._payoffs)
        # print(self._payoffs_covar)
        self.inform("Bot initialised, I have the payoffs for the states.")

    def is_portfolio_optimal(self):
        """
        Returns true if the current holdings are optimal (as per the performance formula), false otherwise.
        :return:
        """
        pass
    
    def get_potential_performance(self, orders):
        """
        Returns the portfolio performance if the given list of orders is executed.
        The performance as per the following formula:
        Performance = ExpectedPayoff - b * PayoffVariance, where b is the penalty for risk.
        :param orders: list of orders
        :return:
        """
        # Check for every potential stock here
        stock_name = ''
        units = 0

        # Initial performance
        self._performace = self._potential_update(stock_name, units)
        
        # Check to buy all stocks
        for key in self._current_stocks.keys():
            curr_performance = self._potential_update(key, 1)
            if curr_performance > self._performace:
                stock_name = key
                units = 1
                self._performace = curr_performance
        # Check to sell all stocks
        for key in self._current_stocks.keys():
            curr_performance = self._potential_update(key, -1)
            if curr_performance > self._performace:
                stock_name = key
                units = -1
                self._performace = curr_performance

        return [stock_name, units]

        

    # Create stock and cash updates to check with formula
    def _potential_update(self, stock_name, units):
        # Units and cash after trade
        stock_copy = self._current_stocks.copy()
        cash_copy = self._cash_avail

        # Get current performance
        if units == 0:
            return self._expected_payoff(stock_copy, cash_copy) - (self._risk_penalty * self._payoff_variance(stock_copy))
        
        # Strategy is reactive first, and proactive if there is no reaction possible
        reactive = True
        # Buying units
        if units > 0:
            # If None, nothing to buy
            if self._current_buy[stock_name] is None:
                reactive = False
                #  If there is nothing in the market, curve tangent price
                if self._current_sell[stock_name] is None:
                    pass

            # If exists, and cash not available
            if not self._cash_check(stock_name, reactive):
                return 0
            if reactive:
                cash_copy -= self._current_buy[stock_name]
            else:
                cash_copy -= self._current_sell[stock_name] - self._profit_margin
            stock_copy[stock_name] += units
        # Selling units
        elif units < 0:
            if self._current_sell[stock_name] is None:
                reactive = False
                if self._current_buy[stock_name] is None:
                    # curve tangent price
                    pass
            if not self._unit_check(stock_name):
                return 0
            if reactive:
                cash_copy += self._current_sell[stock_name]
            stock_copy[stock_name] += units
        # else units == 0, get current performance
        return self._expected_payoff(stock_copy, cash_copy) - (self._risk_penalty * self._payoff_variance(stock_copy))
        
    # Function to calculate expected payoff and return values
    def _expected_payoff(self, stocks, cash):
        payoff_sum = 0
        # Add the average state + number of stocks per state
        for key, value in stocks.items():
            payoff_sum += np.average(self._payoffs[key]) * value
        return cash + payoff_sum

    # Function to calculate payoff variance 
    def _payoff_variance(self, stocks):
        payoff_sum = 0
        # Stock available square * its variance
        for key, value in stocks.items():
            payoff_sum += (value ** 2) * self._payoffs_var[key]
        # 2 * covariance * avail stock 1 * avail stock 2
        for key, value in self._payoffs_covar.items():
            payoff_sum += 2 * value * stocks[key[0]] * stocks[key[1]]
        return payoff_sum

    # Safety check if there are available units to sell
    def _unit_check(self, stock_name):
        return self._current_stocks[stock_name] > 0

    # Safety check if there is cash available to buy
    def _cash_check(self, stock_name, reactive):
        if reactive:
            return (self._cash_avail - self._current_buy[stock_name]) > 0
        # else
        return (self._cash_avail - self._current_sell[stock_name] - self._profit_margin) > 0

    def order_accepted(self, order):
        pass

    def order_rejected(self, info, order):
        pass

    def received_orders(self, orders: List[Order]):
        # Update all orders with current market value every time received orders is called
        print(Order.current().items())

    # Find current minimum and maximum values for each market whenever orders is refreshed
    def _current_market_values(self, items):
        # refresh values to None
        self._refresh_values()
        for _, order in items:
            if order.order_side == OrderSide.BUY:
                self._current_buy[order.market.item] = max((order.price / 100), self._current_buy[order.market.item])
            else:
                self._current_sell = min((order.price / 100), self._current_sell[order.market.item])

    # Refresh values to None for reactive bot
    def _refresh_values(self):
        for key in self._current_buy.keys():
            self._current_buy[key] = None
            self._current_sell[key] = None


    def received_session_info(self, session: Session):
        pass

    def pre_start_tasks(self):
        pass

    def received_holdings(self, holdings):
        self._cash_avail = holdings.cash_available / 100

        # Set stocks
        for market, asset in holdings.assets.items():
            self._current_stocks[market.item] = asset.units_available

        print(f"I have holding cash {holdings.cash} and cash available {holdings.cash_available}")
        for market, asset in holdings.assets.items():
            print(f"Assets settled {asset.units} and available {asset.units_available} for market {market.item}")


if __name__ == "__main__":
    bot = CAPMBot(FM_ACCOUNT, FM_EMAIL, FM_PASSWORD, MARKETPLACE_ID)
    bot.run()
