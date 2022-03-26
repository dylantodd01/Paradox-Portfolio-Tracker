import pandas as pd
import datetime as dt
import yfinance as yf

import plotly.graph_objects as go


class PortfolioTracker:

	def __init__(self):
		self.start_date = dt.date(2022,3,7)
		self.end_date = dt.date.today()
		self.start_cash = 100_000
		
		self.trades_df = pd.read_excel('Trades.xlsx')
		self.SPY = yf.download('SPY', self.start_date, self.end_date)
		self.SPY['Date'] = self.SPY.index

		self.positions = pd.DataFrame(columns = ['Ticker', 'No. Shares', 'Avg Price'])
		self.no_positions = 0


	def calculate_portfolio_performance(self):
		self.portfolio_df = pd.DataFrame()
		self.portfolio_df['Date'] = self.SPY['Date']
		self.portfolio_df['Benchmark'] = 0
		self.portfolio_df['Cash'] = self.start_cash
		self.portfolio_df['Equity'] = self.start_cash

		# Calculate the number of shares of SPY that would have been held over this period
		no_shares_SPY = self.start_cash / self.SPY['Adj Close'].iloc[0]

		# Loop through dates from start date to current date
		for j, date in enumerate(self.portfolio_df['Date']):
			# Calculate benchmark performance
			self.portfolio_df.loc[date, 'Benchmark'] = self.SPY.loc[date, 'Adj Close'] * no_shares_SPY

			# Update the cash balance
			self.portfolio_df['Cash'].iloc[j] = self.portfolio_df['Cash'].iloc[j-1]

			# Loop through trades
			for i, ticker in enumerate(self.trades_df['Ticker']):

				# Check for trade entries
				if date == self.trades_df['Entry Date'][i]:

					# Decreases cash balance when a trade is placed
					if date == self.start_date:
						self.portfolio_df['Cash'].iloc[j] = self.start_cash - self.trades_df['Amount'].iloc[i]
					else:
						self.portfolio_df['Cash'].iloc[j] = self.portfolio_df['Cash'].iloc[j-1] - self.trades_df['Amount'].iloc[i]
					
					# Adds new position to the positions dataframe
					if ticker not in self.positions['Ticker'].values:
						print(ticker)
						no_shares = self.trades_df['Amount'].iloc[i] / self.trades_df['Buy Price'].iloc[i]
						avg_price = self.trades_df['Buy Price'].iloc[i]
						self.positions.loc[len(self.positions)] = [ticker, no_shares, avg_price]

					# Adds to existing position in the positions dataframe
					else:
						no_shares = self.trades_df['Amount'].iloc[i] / self.trades_df['Buy Price'].iloc[i]
						total_no_shares = no_shares + self.positions.loc[self.positions['Ticker'] == ticker, 'No. Shares']
						avg_price = (self.trades_df['Amount'].iloc[i] + (self.positions.loc[self.positions['Ticker'] == ticker, 'No. Shares'] * self.positions.loc[self.positions['Ticker'] == ticker, 'Avg Price'])) / total_no_shares
						self.positions.loc[self.positions['Ticker'] == ticker, 'No. Shares'] = total_no_shares
						self.positions.loc[self.positions['Ticker'] == ticker, 'Avg Price'] = avg_price


				# Check for trade exits
				if date == self.trades_df['Exit Date'][i]:
					print(ticker, "EXIT")


			# Calculate value of current positions
			value = 0
			for i, ticker in enumerate(self.positions['Ticker']):
				close_price = yf.download(ticker, date, date + dt.timedelta(days=1))['Adj Close']
				value += close_price * self.positions['No. Shares'].iloc[i]

			self.portfolio_df['Equity'].iloc[j] = self.portfolio_df['Cash'].iloc[j] + value


	def get_positions(self):
		return self.positions


	def get_performance(self):
		return self.portfolio_df


	def plot(self):
		fig = go.Figure()
		fig.add_trace(go.Scatter(x=self.portfolio_df['Date'], y=self.portfolio_df['Equity'], name='Paradox', mode='lines'))
		fig.add_trace(go.Scatter(x=self.portfolio_df['Date'], y=self.portfolio_df['Benchmark'], name='SPY', mode='lines', opacity=0.35))
		fig.update_layout(
			title="Paradox Performance",
			xaxis_title="Time",
			yaxis_title="Equity",
			font=dict(
        		family="Courier New, monospace",
        		size=18
        	)
        )

		fig.show()


portfolio = PortfolioTracker()
portfolio.calculate_portfolio_performance()


print(portfolio.get_positions())
print(portfolio.get_performance())
portfolio.plot()
