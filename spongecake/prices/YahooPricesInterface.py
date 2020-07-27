import logging
import pandas_datareader as pdr
import pandas as pd
from spongecake.prices.PricesInterface import PricesInterface, PRICES_COLS
from datetime import date, timedelta


class YahooPricesInterface(PricesInterface):

    prices_cache = {}

    def get_yahoo_prices(self, tidm, market='L', from_date=(date.today() - timedelta(days=365)), to_date=date.today(), force_cache_refresh=False):
        if tidm in self.prices_cache.keys() and force_cache_refresh is False:
            logging.info('Found {0} in Yahoo Historic Prices cache returning that instead'.format(tidm))
            return self.prices_cache[tidm]

        from_date_str = from_date.strftime('%Y-%m-%d')
        to_date_str = to_date.strftime('%Y-%m-%d')
        logging.info('Attempting to download historic prices for [{0}] between dates [{1}] and [{2}] from YAHOO'.format(tidm, from_date_str, to_date_str))
        try:
            df_prices = pdr.DataReader('{0}.{1}'.format(tidm,market), 'yahoo', from_date_str, to_date_str)
            logging.info('Downloaded [{0}] prices for [{1}.{2}]'.format(len(df_prices), tidm, market))
        except:
            logging.error('Unable to download prices for [{0}.{1}], you\'ll have to do this manually'.format(tidm, market))
            return pd.DataFrame()
        df_prices = self._remove_duplicate_rows_from_dataframe(df_prices)

        # To sanitise everything (in case we're using multiple price interfaces) rename to a set of standard columns names
        df_prices = self._rename_column(df_prices, YAHOO_DATA_COLUMNS.YHF_CLOSE_COLUMN, PRICES_COLS.COL_CLOSE)
        df_prices = self._rename_column(df_prices, YAHOO_DATA_COLUMNS.YHF_HIGH_COLUMN, PRICES_COLS.COL_HIGH)
        df_prices = self._rename_column(df_prices, YAHOO_DATA_COLUMNS.YHF_LOW_COLUMN, PRICES_COLS.COL_LOW)
        df_prices = self._rename_column(df_prices, YAHOO_DATA_COLUMNS.YHF_OPEN_COLUMN, PRICES_COLS.COL_OPEN)
        df_prices = self._rename_column(df_prices, YAHOO_DATA_COLUMNS.YHF_ADJ_CLOSE_COLUMN, PRICES_COLS.COL_ADJUSTED_CLOSE)

        self.prices_cache[tidm] = df_prices
        return df_prices


class YAHOO_DATA_COLUMNS:
    YHF_CLOSE_COLUMN = 'Close'
    YHF_HIGH_COLUMN = 'High'
    YHF_LOW_COLUMN = 'Low'
    YHF_OPEN_COLUMN = 'Open'
    YHF_ADJ_CLOSE_COLUMN  = 'Adj Close'