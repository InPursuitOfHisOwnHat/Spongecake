# Spongecake Financials
Package that screen-scrapes Fundamentals and calculates a couple of Technicals for UK Equities

# Usage Example - Fundamentals
```
from spongecake.fundamentals import InvestorsChronicleInterface

watchlist = {'VOD': 'Vodfone', 
            'MONY': 'Money Supermarket',
            'TSCO': 'Tesco'}
ic = InvestorsChronicleInterface()
datarows = []
print('Downloading data for: ', end='')
for tidm in watchlist.keys():
    print('[{0}]'.format(tidm), end='')
    datarow = []
    datarow.append(tidm)
    datarow.append(watchlist[tidm])
    datarow.append(ic.get_current_ic_price(tidm))
    datarow.append(ic.get_shares_outstanding(tidm))
    datarow.append(ic.get_market_cap(tidm))
    datarow.append(ic.get_current_ratio(tidm))
    datarow.append(ic.get_total_debt(tidm))
    datarow.append(ic.get_nav_per_share_as_pct_of_price(tidm))
    datarow.append(ic.get_eps(tidm))
    datarow.append(ic.get_eps_ttm(tidm))
    datarow.append(ic.get_price_to_earnings_ratio(tidm))
    datarow.append(ic.get_price_to_earnings_ratio_ttm(tidm))
    datarow.append(ic.get_earnings_yield_pct_ttm(tidm))
    datarow.append(ic.get_earnings_yield_pct(tidm))
    datarow.append(ic.get_roce_pct(tidm))
    
    datarows.append(datarow)
```
# Usage Example - Technicals
```
from spongecake.technicals import YahooPricesInterface, Indicators
ypi = YahooPricesInterface()
indicators = Indicators()
datarows = []
prices_df = ypi.get_yahoo_prices('VOD' + '.L')
prices_df = indicators.set_macd(prices_df)
prices_df = indicators.set_stochastic_oscillator(prices_df)
// Only want today's values?
prices_df = prices_df.tail(1) # Make it one row so we don't have to keep hunting for the tail
```
