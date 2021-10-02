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

from numpy.lib.function_base import average

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

    def initialised(self):
        # Extract payoff distribution for each security
        for _, market_info in self.markets.items():
            security = market_info.item
            description = market_info.description
            self._payoffs[security] = np.array([int(a) for a in description.split(",")]) / 100

        avg_len_div = (1 / len(self._payoffs.keys()))

        # Load payoff squares
        for key, value in self._payoffs.items():
            self._payoffs_square[key] = np.square(value)

        # Load variances
        for key, value in self._payoffs.items():
            self._payoffs_var[key] = (avg_len_div * np.sum(self._payoffs_square[key])) - ((avg_len_div * np.sum(value)) ** 2)

        # Load covariances
        for i in combinations(self._payoffs.keys(), 2):
            payoff1 = self._payoffs[i[0]]
            payoff2 = self._payoffs[i[1]]
            self._payoffs_covar[i] = (np.dot(payoff1, payoff2) * avg_len_div) - (np.average(payoff1) * np.average(payoff2))

        print(self._payoffs)
        # print(self._payoffs_covar)
        self.inform("Bot initialised, I have the payoffs for the states.")

    def get_potential_performance(self, orders):
        """
        Returns the portfolio performance if the given list of orders is executed.
        The performance as per the following formula:
        Performance = ExpectedPayoff - b * PayoffVariance, where b is the penalty for risk.
        :param orders: list of orders
        :return:
        """
        pass

    # Function to check for every purchase in current market possible
    def _expected_payoff(self):
        # Expected payoff given by current market prices
        pass

    def is_portfolio_optimal(self):
        """
        Returns true if the current holdings are optimal (as per the performance formula), false otherwise.
        :return:
        """
        pass

    def order_accepted(self, order):
        pass

    def order_rejected(self, info, order):
        pass

    def received_orders(self, orders: List[Order]):
        print(Order.current().items())

    # Find current minimum and maximum values for each market whenever orders is refreshed
    def _current_market_values(self, items):
        # refresh values to 0s
        self._refresh_values()
        for _, order in items:
            if order.order_side == OrderSide.BUY:
                self._current_buy[order.market.item] = max((order.price / 100), self._current_buy[order.market.item])
            else:
                self._current_sell = min((order.price / 100), self._current_sell[order.market.item])

    # Refresh value with each holding
    def _refresh_values(self):
        for key in self._current_buy.keys():
            self._current_buy[key] = 0
            self._current_sell[key] = 10.0
        # Maximum for note is 5.0
        self._current_sell['note'] = 5.0


    def received_session_info(self, session: Session):
        pass

    def pre_start_tasks(self):
        pass

    def received_holdings(self, holdings):
        self._cash_avail = holdings.cash_available

        # Set stocks
        for market, asset in holdings.assets.items():
            self._current_stocks[market.item] = asset.units_available

        print(f"I have holding cash {holdings.cash} and cash available {holdings.cash_available}")
        for market, asset in holdings.assets.items():
            print(f"Assets settled {asset.units} and available {asset.units_available} for market {market.item}")


if __name__ == "__main__":
    bot = CAPMBot(FM_ACCOUNT, FM_EMAIL, FM_PASSWORD, MARKETPLACE_ID)
    bot.run()
