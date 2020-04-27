from spongecake.technicals.PricesInterface import PRICES_COLS
import logging
import pandas as pd


class Indicators:

    @staticmethod
    def set_stochastic_oscillator(df_prices, slow_periods=14, fast_periods=3):
        if len(df_prices) <= 0:
            logging.error('error: you need a set of prices in the \'price_data\' field of the company before you can calculate the Stochastic Oscillator.')
            return pd.DataFrame()
        df_prices[INDICATOR_COLS.COL_STOCHASTIC_OSCILLATOR_K_COLUMN] = ((df_prices[PRICES_COLS.COL_CLOSE] - df_prices[PRICES_COLS.COL_LOW].rolling(slow_periods).min()) /
                                                                              (df_prices[PRICES_COLS.COL_HIGH].rolling(slow_periods).max() - df_prices[PRICES_COLS.COL_LOW].rolling(slow_periods).min())) * 100
        df_prices[INDICATOR_COLS.COL_STOCHASTIC_OSCILLATOR_D_COLUMN] = df_prices[INDICATOR_COLS.COL_STOCHASTIC_OSCILLATOR_K_COLUMN].rolling(fast_periods).mean()
        return df_prices

    @staticmethod
    def set_macd(df_prices, long_period=26, short_period=3, signal_period=9):
        if len(df_prices) <= 0:
            logging.error('error: you need a set of prices in the \'price_data\' field of the company before you can calculate the Stochastic Oscillator.')
            return
        df_prices[INDICATOR_COLS.COL_MACD_COLUMN] = \
            (df_prices[PRICES_COLS.COL_CLOSE]).ewm(span=short_period, adjust=False, min_periods=short_period).mean() - \
            (df_prices[PRICES_COLS.COL_CLOSE]).ewm(span=long_period, adjust=False, min_periods=long_period).mean()
        df_prices[INDICATOR_COLS.COL_MACD_SIGNAL_COLUMN] = df_prices[INDICATOR_COLS.COL_MACD_COLUMN].ewm(span=signal_period, adjust=False, min_periods=signal_period).mean()
        return df_prices


class INDICATOR_COLS:

    COL_STOCHASTIC_OSCILLATOR_K_COLUMN = 'STO_K'
    COL_STOCHASTIC_OSCILLATOR_D_COLUMN = 'STO_D'

    COL_MACD_COLUMN = 'MACD'
    COL_MACD_SIGNAL_COLUMN = 'MACD_SIGNAL'