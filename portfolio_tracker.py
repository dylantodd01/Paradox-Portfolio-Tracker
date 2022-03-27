import pandas as pd
import datetime as dt
import yfinance as yf

import plotly.graph_objects as go
from plotly.subplots import make_subplots


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

		self.ATH = 0 # Set an all time high variable for drawdown calculations


	def calculate_portfolio_performance(self):
		self.portfolio_df = pd.DataFrame()
		self.portfolio_df['Date'] = self.SPY['Date']
		self.portfolio_df['Benchmark'] = 0
		self.portfolio_df['Cash'] = self.start_cash
		self.portfolio_df['Equity'] = self.start_cash
		self.portfolio_df['Drawdown'] = 0

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
			# Calculate current equity
			self.portfolio_df['Equity'].iloc[j] = self.portfolio_df['Cash'].iloc[j] + value

			# Check for new all time high
			self.ATH = max(self.ATH, self.portfolio_df['Equity'].iloc[j])
			# Calculate current drawdown (%)
			self.portfolio_df['Drawdown'].iloc[j] = ((self.portfolio_df['Equity'].iloc[j] / self.ATH) - 1) * 100


			


	def get_positions(self):
		return self.positions


	def get_performance(self):
		return self.portfolio_df


	def get_holdings(self):
		"""
		Generate easily accessible holdings data for the pie chart
		"""
		holdings = ['Cash'] + [ticker for ticker in self.positions['Ticker']]
		amounts = [self.portfolio_df['Cash'].iloc[-1]] + [(no_shares * self.positions['Avg Price'].iloc[i]) for i, no_shares in enumerate(self.positions['No. Shares'])]
		return (holdings, amounts)



	def plot(self):
		#fig = go.Figure()
		fig = make_subplots(
		    rows=2, cols=2,
		    specs=[[{"colspan": 2}, None],
		    	[{"type": "xy"}, {"type": "domain"}]],
		    subplot_titles=("Paradox Performance", "Drawdown", "Holdings"),
		    column_widths=[0.65, 0.35]
		)
		fig.update_annotations(font_size=30)

		fig.add_trace(go.Scatter(x=self.portfolio_df['Date'], y=self.portfolio_df['Equity'], name='Paradox', mode='lines', legendgroup=1), row=1, col=1)
		fig.add_trace(go.Scatter(x=self.portfolio_df['Date'], y=self.portfolio_df['Benchmark'], name='SPY', mode='lines', opacity=0.35, legendgroup=1), row=1, col=1)

		fig.add_trace(go.Scatter(x=self.portfolio_df['Date'], y=self.portfolio_df['Drawdown'], mode='lines', fill='tozeroy', showlegend=False), row=2, col=1)

		holdings, amounts = self.get_holdings()
		fig.add_trace(go.Pie(labels=holdings, values=amounts, textinfo='label+percent', insidetextorientation='radial', rotation=90, legendgroup=2), row=2, col=2)

		# Update xaxis properties
		fig.update_yaxes(title_text="Equity", row=1, col=1)
		fig.update_yaxes(title_text="Drawdown %", row=2, col=1)

		fig.update_layout(
			font=dict(
        		family="Courier New, monospace",
        		size=18
        	),
        	showlegend=True,
        	legend_tracegroupgap=400
        )

		fig.show()


portfolio = PortfolioTracker()
portfolio.calculate_portfolio_performance()


print(portfolio.get_positions())
print(portfolio.get_performance())
portfolio.plot()
