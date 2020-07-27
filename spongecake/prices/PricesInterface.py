import pandas as pd

class PricesInterface:

    @staticmethod
    def _rename_column(df_prices, old_name, new_name):
        return df_prices.rename(columns={old_name : new_name})

    @staticmethod
    def _remove_duplicate_rows_from_dataframe(df: pd.DataFrame()):
        no_dups = df[~df.index.duplicated(keep='first')]
        dup_diff = len(df) - len(no_dups)
        if dup_diff > 0:
            df = no_dups
        return df


class PRICES_COLS:
    COL_CLOSE = 'CLOSE'
    COL_HIGH = 'HIGH'
    COL_LOW = 'LOW'
    COL_ADJUSTED_CLOSE = 'ADJ CLOSE'
    COL_OPEN = 'OPEN'


