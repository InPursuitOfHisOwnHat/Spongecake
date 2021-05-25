import logging as log
import pandas as pd
from datetime import datetime
from spongecake.fundamentals.FinancialWebsiteInterface import FinancialWebsiteInterface


class InvestorsChronicleInterface(FinancialWebsiteInterface):

    '''
    Provides an interface to the Investors Chronicle website which provides
    free fundamental information about various equities.

    There are roughly four sections downloaded and cached:

        * Income (Income Sheet details)
        * Balance (Balance Sheet details)
        * Summary (Misc information about the stock)
        * Price (Stock prices)

    Each section is cached for each stock the first time it's retrieved and
    never refreshed unless forced. Once exception to this is the stock price
    which is cached for a max of 5 mins. Even then, it is only refreshed if a
    subsequent call is made to retrieve it.

    This class also provides a number of functions that will generate certain,
    well-known fundamental calculations (e.g. EPS).

    '''
    # To always pull data fresh from the website set this value to True.

    disable_all_caching = False

    # Seconds that we allow a price to stay valid for in the cache which is
    # currently 5 mins (300 Seconds)

    maximum_price_cache_age = 300

    # These are all dictionaries that will store data keyed with the tidm
    # (tradable mnemonic of the stock)

    price_cache = {}
    income_cache = {}
    balance_cache = {}
    summary_cache = {}

    # Where does the data come from?

    INCOME_URL = 'https://markets.investorschronicle.co.uk/data/equities/tearsheet/financials?s={TIDM}:{MARKET}&subview=IncomeStatement'
    BALANCE_URL = 'https://markets.investorschronicle.co.uk/data/equities/tearsheet/financials?s={TIDM}:{MARKET}&subview=BalanceSheet'
    SUMMARY_URL = 'https://markets.investorschronicle.co.uk/data/equities/tearsheet/summary?s={TIDM}:{MARKET}'


    def __format_ic_income_dataframe(self, df_income):
        income_lines_column_name = df_income.columns[0]
        log.info('Renaming income sheet column [{0}] to [{1}]'.format(income_lines_column_name, IC_INCOME_DATA.NEW_INCOME_LINE_ITEM_COLUMN_NAME))
        df_income = df_income.rename(columns={income_lines_column_name: IC_INCOME_DATA.NEW_INCOME_LINE_ITEM_COLUMN_NAME})
        df_income.set_index(IC_INCOME_DATA.NEW_INCOME_LINE_ITEM_COLUMN_NAME, inplace=True)

        # Need to replace all figures in parentheses as - (minus) numbers so we
        # can convert to numeric later
        
        for col in df_income.columns:
            df_income[col] = df_income[col].replace( '[\$,)]', '', regex=True ).replace('[(]', '-', regex=True)

        df_income = df_income.apply(pd.to_numeric, errors='coerce').dropna(how='all')
        return df_income


    def __format_ic_balance_dataframe(self, df_balance):
        income_lines_column_name = df_balance.columns[0]
        log.info('Renaming balance sheet column [{0}] to [{1}]'.format(income_lines_column_name, IC_BALANCE_DATA.NEW_BALANCE_LINE_ITEM_COLUMN_NAME))
        df_balance = df_balance.rename(columns={income_lines_column_name: IC_BALANCE_DATA.NEW_BALANCE_LINE_ITEM_COLUMN_NAME})

        # Need to replace all figures in parentheses as - (minus) numbers so we
        # can convert to numeric later
        
        for col in df_balance.columns:
            df_balance[col] = df_balance[col].replace( '[\$,)]', '', regex=True ).replace('[(]', '-', regex=True)

        df_balance.set_index(IC_BALANCE_DATA.NEW_BALANCE_LINE_ITEM_COLUMN_NAME, inplace=True)
        df_balance = df_balance.apply(pd.to_numeric, errors='coerce').dropna(how='all')
        return df_balance


    def __format_ic_summary_dataframe(self, df_summary):
        log.info('Renaming summary sheet columns from 0 and 1 to [{0}] and [{1}]'.format(IC_SUMMARY_DATA.NEW_SUMMARY_LINE_ITEM_COLUMN_NAME, IC_SUMMARY_DATA.NEW_SUMMARY_VALUE_COLUMN_NAME))
        df_summary = df_summary.rename(columns={0: IC_SUMMARY_DATA.NEW_SUMMARY_LINE_ITEM_COLUMN_NAME, 1: IC_SUMMARY_DATA.NEW_SUMMARY_VALUE_COLUMN_NAME})
        df_summary.set_index(IC_SUMMARY_DATA.NEW_SUMMARY_LINE_ITEM_COLUMN_NAME, inplace=True)
        return df_summary


    def get_ic_income_sheet(self, tidm, market='LSE'):
        '''
        Scrape income data for a particular stock from the Investors Chronicle
        website and store in cache for later access.

        Parameters:

            tidm: Display mnemonic of stock
            market: Market code where stock is traded (default to London)

        Returns:

            A Pandas Dataframe of income sheet data (Note that not all of 
            these columns may be present:

                Total revenue
                Cost of revenue total
                Selling, general and admin. expenses, total
                Unusual expense(income)
                Other operating expenses, total
                Total operating expense
                Operating income
                Other, net
                Net income before taxes
                Provision for income taxes
                Net income after taxes
                Minority interest
                Net income before extra. Items
                Total extraordinary items
                Net income
                Inc.avail. to common excl. extra. Items
                Inc.avail. to common incl. extra. Items
                Basic/primary weighted average shares
                Basic/primary eps excl. extra items
                Basic/primary eps incl. extra items
                Diluted weighted average shares
                Diluted eps excl. extra items
                Diluted eps incl. extra items
                DPS - common stock primary issue
                Gross dividend - common stock
                Interest expense, supplemental
                Depreciation, supplemental
                Total special items
                Normalized income before taxes
                Effect of special items on income taxes
                Income tax excluding impact of special items
                Normalized income after tax
                Normalized income avail. to common
                Basic normalized EPS
                Diluted normalized EPS
        '''
        # Pull from cache first if it exists
        cache_key = '{0}:{1}'.format(tidm, market)
        if not self.disable_all_caching and cache_key in self.income_cache.keys():
            log.info('Found {0} in income sheet cache, returning cached version of sheet instead'.format(cache_key))
            return self.income_cache[cache_key]

        log.info('{0} not found in income sheet cache, getting from website.'.format(cache_key))

        url = self.INCOME_URL.format(TIDM=tidm, MARKET=market)
        log.info('Calling following URL for {0} income sheet: {1}'.format(tidm, url))
        raw_html = self.download_web_page(url)
        log.info('Extracting tables from {0} income sheet'.format(tidm))
        html_tables = self.extract_tables_from_raw_html(raw_html)
        log.info('Extracted {0} tables.'.format(len(html_tables)))

        income_dataframes = self.get_dataframes_from_html_tables(html_tables)

        # There should only be one DataFrame returned, really
        if len(income_dataframes) > 1:
            log.warning('There appear to be more than 1 dataframes in the list returned for the income sheet: {0}'.format(len(income_dataframes)))

        df_income = income_dataframes[IC_INCOME_DATA.INCOME_DATA_FRAME_INDEX]
        df_income = self.__format_ic_income_dataframe(df_income)

        # Add to cache for later
        self.income_cache['{0}:{1}'.format(tidm, market)] = df_income
        return df_income


    def get_ic_balance_sheet(self, tidm, market='LSE'):
        '''
        Scrape balance sheet data for a particular stock from the Investors
        Chronicle website and store in cache for later access.

        Parameters:

            tidm: Display mnemonic of stock
            market: Market code where stock is traded (default to London)

        Returns:

            A Pandas Dataframe of balance sheet data (Note that not all of 
            these columns may be present:

                Cash And Short Term Investments
                Total Receivables Net
                Total Inventory
                Prepaid expenses
                Other current assets total
                Total current assets
                Property plant & equipment net
                Goodwill net
                Intangibles net
                Long term investments
                Note receivable - long term
                Total assets
                Accounts payable
                Accrued expenses
                Notes payable/short-term debt
                Current portion long-term debt/capital leases
                Other current liabilities total
                Total current liabilities
                Total long term debt
                Total debt
                Deferred income tax
                Minority interest
                Other liabilities total
                Total liabilities
                Common stock
                Additional paid-in capital
                Retained earnings -accumulated deficit
                Treasury stock - common
                Unrealized gain -loss
                Other equity total
                Total equity
                Total liabilities & shareholders' equity
                Total common shares outstanding
                Treasury shares - common primary issue
        '''
        # Pull from cache first if it exists
        cache_key = '{0}:{1}'.format(tidm, market)
        if not self.disable_all_caching and cache_key in self.balance_cache.keys():
            log.info('Found {0} in balance sheet cache, returning cached version of sheet instead'.format(cache_key))
            return self.balance_cache[cache_key]

        log.info('{0} not found in balance sheet cache, getting from website.'.format(cache_key))

        url = self.BALANCE_URL.format(TIDM=tidm, MARKET=market)
        log.info('Calling following URL for {0} balance sheet: {1}'.format(tidm, url))
        raw_html = self.download_web_page(url)
        log.info('Extracting tables from {0} balance sheet'.format(tidm))
        html_tables = self.extract_tables_from_raw_html(raw_html)
        log.info('Extracted {0} tables.'.format(len(html_tables)))

        balance_dataframes = self.get_dataframes_from_html_tables(html_tables)

        # There should only be one DataFrame returned, really
        if len(balance_dataframes) > 1:
            log.warning('There appear to be more than 1 dataframes in the list returned for the balance sheet: {0}'.format(len(balance_dataframes)))

        df_balance = balance_dataframes[IC_BALANCE_DATA.BALANCE_DATA_FRAME_INDEX]
        df_balance = self.__format_ic_balance_dataframe(df_balance)

        self.balance_cache['{0}:{1}'.format(tidm, market)] = df_balance
        return df_balance


    def get_ic_summary_sheet(self, tidm, market='LSE'):
        '''
        Scrape summary sheet data for a particular stock from the Investors
        Chronicle website and store in cache for later access.

        Parameters:

            tidm: Display mnemonic of stock
            market: Market code where stock is traded (default to London)

        Returns:

            A Pandas Dataframe of summary sheet data (Note that not all of 
            these columns may be present:
   
                Open
                High
                Low
                Bid
                Offer
                Previous close
                Average volume
                Shares outstanding
                Free float
                P/E (TTM)
                Market cap
                EPS (TTM)
                Annual div (ADY)
                Annual div yield (ADY)
                Div ex-date
                Div pay-date
                Next div ex-date
                Next div pay-date
        '''
        # Pull from cache first if it exists
        cache_key = '{0}:{1}'.format(tidm, market)
        if cache_key in self.summary_cache.keys():
            log.info('Found {0} in summary sheet cache, returning cached version of sheet instead'.format(cache_key))
            return self.summary_cache[cache_key]

        log.info('{0} not found in summary sheet cache, getting from website.'.format(cache_key))

        url = self.SUMMARY_URL.format(TIDM=tidm, MARKET=market)
        log.info('Calling following URL for {0} summary sheet: {1}'.format(tidm, url))
        raw_html = self.download_web_page(url)
        log.info('Extracting tables from {0} summary sheet'.format(tidm))
        html_tables = self.extract_tables_from_raw_html(raw_html)
        log.info('Extracted {0} tables.'.format(len(html_tables)))

        summary_dataframes = self.get_dataframes_from_html_tables(html_tables, headers=None)

        # There should be 3 DataFrames returned for this page but they can all be merged into 1 as it's just 'Item'|'Value'
        if len(summary_dataframes) > 3:
            log.warning('There appear to be more than 3 dataframes in the list returned for the summary sheet: {0}'.format(len(summary_dataframes)))

        log.info('Merging all Dataframes into 1')
        merged_summaries = pd.concat(summary_dataframes)

        log.info('Formatting final Dataframe.')
        merged_formatted_summaries = self.__format_ic_summary_dataframe(merged_summaries)

        self.summary_cache['{0}:{1}'.format(tidm, market)] = merged_formatted_summaries
        return merged_formatted_summaries


    def get_current_ic_price(self, tidm, market='LSE'):
        '''
        Extract current share price for a particular stock from the Investors 
        Chronicle website.

        The share price is cached for a default of 5mins (3000ms). This can be
        modified by changing the 'maximum_price_cache_age' field, above.

        Parameters:

            tidm: Display mnemonic of stock
            market: Market code where stock is traded (default to London)

        Returns:

            Price of the selected stock.

        '''
        # Pull from cache first if it exists and is young enough
        cache_key = '{0}:{1}'.format(tidm, market)
        if cache_key in self.price_cache.keys():
            log.info('Found {0} in price cache. Checking age.'.format(cache_key))
            cached_price = self.price_cache[cache_key]
            delta = datetime.now() - cached_price[0]
            log.info('Ages is {0} seconds'.format(delta.seconds))
            if delta.seconds <= self.maximum_price_cache_age:
                log.info('Age is less than current maximum of {0}, so using cached version.'.format(self.maximum_price_cache_age))
                return self.price_cache[cache_key][1]

        url = self.SUMMARY_URL.format(TIDM=tidm, MARKET=market)
        log.info('Calling following URL for {0} price: {1}'.format(tidm, url))
        raw_html = self.download_web_page(url)

        start_pos = raw_html.find(IC_SUMMARY_DATA.PRICE_START_SEARCH_STRING)
        if start_pos == -1:
            log.error('Couldn''t find the start_pos search pattern in the html returned.')
            return 0.0

        start_pos = start_pos + len(IC_SUMMARY_DATA.PRICE_START_SEARCH_STRING)
        end_pos = raw_html.find(IC_SUMMARY_DATA.PRICE_END_SEARCH_STRING, start_pos)

        if end_pos == -1:
            log.error('Couldn''t find the end_pos search pattern in the html returned.')
            return 0.0

        price = float(raw_html[start_pos:end_pos].replace(',', ''))
        self.price_cache[cache_key] = (datetime.now(), price)
        return price


    def get_date_of_latest_income_sheet(self, tidm, market='LSE'):
        '''
        Allows you to find out how old data in the income sheet actually is.

        Parameters:

            tidm: Display mnemonic of stock
            market: Market code where stock is traded (default to London)

        Returns:

            The latest date found on the income sheet
        '''
        df_income = self.get_ic_income_sheet(tidm, market)
        return df_income.columns.max()


    def get_date_of_latest_balance_sheet(self, tidm, market='LSE'):
        '''
        Allows you to find out how old data in the balance sheet actually is.

        Parameters:

            tidm: Display mnemonic of stock
            market: Market code where stock is traded (default to London)

        Returns:

            The latest date found on the balance sheet
        '''
        df_balance = self.get_ic_balance_sheet(tidm, market)
        return df_balance.columns.max()


    def get_roce_pct(self, tidm, market='LSE'):
        '''
        Get the current Return on Capital Employed as a percentage

        Parameters:

            tidm: Display mnemonic of stock
            market: Market code where stock is traded (default to London)

        Returns:

            ROCE value as a float percentage, e.g. will return '0.10', not '10%')

        '''
        df_income = self.get_ic_income_sheet(tidm, market)
        df_balance = self.get_ic_balance_sheet(tidm, market)

        latest_data = max(df_income.columns)

        income_before_tax = df_income.loc[IC_INCOME_DATA.ROW_NET_INCOME_BEFORE_TAXES][latest_data]
        log.info('Got income before tax for {0} at {1}'.format(tidm, income_before_tax))

        total_assets = df_balance.loc[IC_BALANCE_DATA.ROW_TOTAL_ASSETS][latest_data]
        log.info('Got total assets for {0} at {1}'.format(tidm, total_assets))

        current_liabilities = df_balance.loc[IC_BALANCE_DATA.ROW_TOTAL_CURRENT_LIABILITIES][latest_data]
        log.info('Got current liabilities for {0} at {1}'.format(tidm, current_liabilities))

        captial_employed = total_assets - current_liabilities
        roce = income_before_tax / captial_employed

        return roce


    def get_shares_outstanding(self, tidm, market='LSE'):
        '''
        Get Shares outstanding.

        Note that the value is converted from a text string in the data which is
        usually an integer followed by either 'M' (million) or 'N' (billion).
        The value is converted to the actual number (e.g., '10M' becomes
        '10000000').

        Parameters:

            tidm: Display mnemonic of stock
            market: Market code where stock is traded (default to London)

        Returns:

            Shares outstanding value as float

        '''
        df_summary = self.get_ic_summary_sheet(tidm, market)
        str_shares_outstanding = df_summary.loc[IC_SUMMARY_DATA.ROW_SHARES_OUTSTANDING][IC_SUMMARY_DATA.NEW_SUMMARY_VALUE_COLUMN_NAME]
        log.info('Got Shares Outstanding value for {0}: {1}'.format(tidm, str_shares_outstanding))
        shares_outstanding_unit = str_shares_outstanding[-1:].upper()
        log.info('Unit is: {0}'.format(shares_outstanding_unit))

        if shares_outstanding_unit == 'M':
            shares_outstanding = float(str_shares_outstanding[:-1]) * 1000000
        elif shares_outstanding_unit == 'N':
            shares_outstanding = float(str_shares_outstanding[:-2]) * 1000000000
        else:
            log.error('Unrecognised unit used for Shares Outstanding for {0}: {1}'.format(tidm, shares_outstanding_unit))
            shares_outstanding = 0

        return shares_outstanding


    def get_price_to_earnings_ratio_ttm(self, tidm, market='LSE'):
        '''
        Get Time to Market Price to Earnings Ratio

        Parameters:

            tidm: Display mnemonic of stock
            market: Market code where stock is traded (default to London)

        Returns:

            Price to Earnings ratio as float
        '''
        df_summary = self.get_ic_summary_sheet(tidm, market)
        str_price_to_earnings_ratio_ttm = df_summary.loc[IC_SUMMARY_DATA.ROW_P_E_TTM_][IC_SUMMARY_DATA.NEW_SUMMARY_VALUE_COLUMN_NAME]
        if str_price_to_earnings_ratio_ttm == '--':
            return 0

        return float(str_price_to_earnings_ratio_ttm)


    def get_price_to_earnings_ratio(self, tidm, market='LSE'):
        '''
        Get Price to Earnings Ratio

        Parameters:

            tidm: Display mnemonic of stock
            market: Market code where stock is traded (default to London)

        Returns:

            Price to Earnings ratio as float
        '''
        log.info('Calculating price to earnings ratio for {0}')
        eps = self.get_eps(tidm, market)
        log.info('EPS for {0} is: '.format(eps))
        price = (self.get_current_ic_price(tidm, market)) / 100
        log.info('Price for {0} is: {1}'.format(tidm, price))

        per = price / eps
        return per


    def get_eps_ttm(self, tidm, market='LSE'):
        '''
        Get Earnings Per Share Time to Market (EPS)

        Parameters:

            tidm: Display mnemonic of stock
            market: Market code where stock is traded (default to London)

        Returns:

            Earnings Per Share (TTM) as float.
        '''
        df_summary = self.get_ic_summary_sheet(tidm, market)
        str_eps_ttm = df_summary.loc[IC_SUMMARY_DATA.ROW_EPS_TTM_][IC_SUMMARY_DATA.NEW_SUMMARY_VALUE_COLUMN_NAME]
        if str_eps_ttm == '--':
            return 0.0

        # Lop off the 'GBP' at the end of the line
        return float(str_eps_ttm[:-4])


    def get_eps(self, tidm, market='LSE'):
        '''
        Get Earnings Per Share (EPS)

        Parameters:

            tidm: Display mnemonic of stock
            market: Market code where stock is traded (default to London)

        Returns:

            Earnings Per Share as float.
        '''
        log.info('Getting EPS for {0}'.format(tidm))
        shares_outstanding = self.get_shares_outstanding(tidm, market)
        log.info('Shares Outstanding for {0} is: {1}'.format(tidm, shares_outstanding))
        df_income = self.get_ic_income_sheet(tidm, market)
        latest_data = max(df_income.columns)
        ebit = float(df_income.loc[IC_INCOME_DATA.ROW_NET_INCOME_BEFORE_TAXES][latest_data]) * 1000000
        log.info('EBIT for {0} is: {1}'.format(tidm, ebit))

        # Price is in Pence, remember
        eps = ebit / shares_outstanding
        return eps


    def get_earnings_yield_pct_ttm(self, tidm, market='LSE'):
        '''
        Get Earnings Yield Time to Market as a Percentage

        Parameters:

            tidm: Display mnemonic of stock
            market: Market code where stock is traded (default to London)

        Returns:

            Earnings Yield Time to Market as a float percentage (e.g. will 
            return '0.10', not '10%')
        '''
        eps_ttm = self.get_eps_ttm(tidm, market)
        if eps_ttm == 0:
            return 0
        price = self.get_current_ic_price(tidm, market)

        # Price is in Pence, remember
        ey_ttm = eps_ttm / (price / 100)
        return ey_ttm


    def get_earnings_yield_pct(self, tidm, market='LSE'):
        '''
        Get Earnings Yield as a Percentage

        Parameters:

            tidm: Display mnemonic of stock
            market: Market code where stock is traded (default to London)

        Returns:

            Earnings Yield as a float percentage (e.g. will return '0.10', not '10%')
        '''
        eps = self.get_eps(tidm, market)
        price = self.get_current_ic_price(tidm, market)

        # Price is in Pence, remember
        ey = eps / (price / 100)
        return ey


    def get_total_debt(self, tidm, market='LSE'):
        '''
        Get Total Debt Owed

        Parameters:

            tidm: Display mnemonic of stock
            market: Market code where stock is traded (default to London)

        Returns:

            Total Debt Owed as a float
        '''
        df_balance = self.get_ic_balance_sheet(tidm, market)
        latest_data = max(df_balance.columns)
        str_total_debt = df_balance.loc[IC_BALANCE_DATA.ROW_TOTAL_DEBT][latest_data]
        return float(str_total_debt)


    def get_current_ratio(self, tidm, market='LSE'):
        '''
        Get Current Ratio

        Parameters:

            tidm: Display mnemonic of stock
            market: Market code where stock is traded (default to London)

        Returns:

            Current Ratio as float
        '''
        df_balance = self.get_ic_balance_sheet(tidm, market)
        latest_data = max(df_balance.columns)
        current_liabilities = df_balance.loc[IC_BALANCE_DATA.ROW_TOTAL_CURRENT_LIABILITIES][latest_data]
        current_assets = df_balance.loc[IC_BALANCE_DATA.ROW_TOTAL_CURRENT_ASSETS][latest_data]
        current_ratio = float(current_assets) / float(current_liabilities)
        return current_ratio


    def get_nav(self, tidm, market='LSE'):
        '''
        Get Net Asset Value

        Parameters:

            tidm: Display mnemonic of stock
            market: Market code where stock is traded (default to London)

        Returns:

            Net Asset Value as float
        '''
        df_balance = self.get_ic_balance_sheet(tidm, market)
        latest_data = max(df_balance.columns)

        total_assets = df_balance.loc[IC_BALANCE_DATA.ROW_TOTAL_ASSETS][latest_data]
        total_liabilities = df_balance.loc[IC_BALANCE_DATA.ROW_TOTAL_LIABILITIES][latest_data]

        net_asset_value = float(total_assets) - float(total_liabilities)
        return net_asset_value


    def get_nav_per_share(self, tidm, market='LSE'):
        '''
        Get Net Asset Value Per Share

        Parameters:

            tidm: Display mnemonic of stock
            market: Market code where stock is traded (default to London)

        Returns:

            Net Asset Value Per Share as float
        '''
        log.info('Calculating NAV Per Share for {0}'.format(tidm))
        nav = self.get_nav(tidm, market) * 1000000
        log.info('NAV for {0}: {1}'.format(tidm, nav))
        shares_outstanding = self.get_shares_outstanding(tidm, market)
        log.info('Shares outstanding for {0}: {1}'.format(tidm, shares_outstanding))
        nav_per_share = nav / float(shares_outstanding)
        return nav_per_share


    def get_nav_per_share_as_pct_of_price(self, tidm, market='LSE'):
        '''
        Get Net Asset Per Share as a percentage of the current share price

        Parameters:

            tidm: Display mnemonic of stock
            market: Market code where stock is traded (default to London)

        Returns:

            Net Asset Per Share as a percentage of the current share price, as float
        '''
        nav_per_share = self.get_nav_per_share(tidm, market)
        # Remember, price is in GBX
        price = self.get_current_ic_price(tidm, market) / 100
        pct = (nav_per_share / price)
        return pct


    def get_market_cap(self, tidm, market='LSE'):
        '''
        Get Market Capitalisation

        Parameters:

            tidm: Display mnemonic of stock
            market: Market code where stock is traded (default to London)

        Returns:

            Market Capitalisation as float
        '''
        price = self.get_current_ic_price(tidm, market) / 100
        shares_outstanding = self.get_shares_outstanding(tidm, market)
        market_cap = price * shares_outstanding
        return market_cap


class IC_SUMMARY_DATA:
    PRICE_START_SEARCH_STRING = 'Price (GBX)</span><span class="mod-ui-data-list__value">'
    PRICE_END_SEARCH_STRING = '</span>'
    NEW_SUMMARY_LINE_ITEM_COLUMN_NAME = 'Summary Line Item'
    NEW_SUMMARY_VALUE_COLUMN_NAME = 'Value'

    # DATA ROWS
    ROW_OPEN = "Open"
    ROW_HIGH = "High"
    ROW_LOW = "Low"
    ROW_BID = "Bid"
    ROW_OFFER = "Offer"
    ROW_PREVIOUS_CLOSE = "Previous close"
    ROW_AVERAGE_VOLUME = "Average volume"
    ROW_SHARES_OUTSTANDING = "Shares outstanding"
    ROW_FREE_FLOAT = "Free float"
    ROW_P_E_TTM_ = "P/E (TTM)"
    ROW_MARKET_CAP = "Market cap"
    ROW_EPS_TTM_ = "EPS (TTM)"
    ROW_ANNUAL_DIV_ADY_ = "Annual div (ADY)"
    ROW_ANNUAL_DIV_YIELD_ADY_ = "Annual div yield (ADY)"
    ROW_DIV_EXDATE = "Div ex-date"
    ROW_DIV_PAYDATE = "Div pay-date"


class IC_INCOME_DATA:
    INCOME_DATA_FRAME_INDEX = 0
    NEW_INCOME_LINE_ITEM_COLUMN_NAME = 'Income Line Item'

    # DATA ROWS
    ROW_TOTAL_REVENUE = "Total revenue"
    ROW_COST_OF_REVENUE_TOTAL = "Cost of revenue total"
    ROW_SELLING_GENERAL_AND_ADMIN_EXPENSES_TOTAL = "Selling, general and admin. expenses, total"
    ROW_DEPRECIATION_AMORTIZATION = "Depreciation/amortization"
    ROW_UNUSUAL_EXPENSE_INCOME_ = "Unusual expense(income)"
    ROW_OTHER_OPERATING_EXPENSES_TOTAL = "Other operating expenses, total"
    ROW_TOTAL_OPERATING_EXPENSE = "Total operating expense"
    ROW_OPERATING_INCOME = "Operating income"
    ROW_OTHER_NET = "Other, net"
    ROW_NET_INCOME_BEFORE_TAXES = "Net income before taxes"
    ROW_PROVISION_FOR_INCOME_TAXES = "Provision for income taxes"
    ROW_NET_INCOME_AFTER_TAXES = "Net income after taxes"
    ROW_MINORITY_INTEREST = "Minority interest"
    ROW_NET_INCOME_BEFORE_EXTRA_ITEMS = "Net income before extra. Items"
    ROW_TOTAL_EXTRAORDINARY_ITEMS = "Total extraordinary items"
    ROW_NET_INCOME = "Net income"
    ROW_INCAVAIL_TO_COMMON_EXCL_EXTRA_ITEMS = "Inc.avail. to common excl. extra. Items"
    ROW_INCAVAIL_TO_COMMON_INCL_EXTRA_ITEMS = "Inc.avail. to common incl. extra. Items"
    ROW_EPS_RECONCILIATION = "EPS RECONCILIATION"
    ROW_BASIC_PRIMARY_WEIGHTED_AVERAGE_SHARES = "Basic/primary weighted average shares"
    ROW_BASIC_PRIMARY_EPS_EXCL_EXTRA_ITEMS = "Basic/primary eps excl. extra items"
    ROW_BASIC_PRIMARY_EPS_INCL_EXTRA_ITEMS = "Basic/primary eps incl. extra items"
    ROW_DILUTION_ADJUSTMENT = "Dilution adjustment"
    ROW_DILUTED_WEIGHTED_AVERAGE_SHARES = "Diluted weighted average shares"
    ROW_DILUTED_EPS_EXCL_EXTRA_ITEMS = "Diluted eps excl. extra items"
    ROW_DILUTED_EPS_INCL_EXTRA_ITEMS = "Diluted eps incl. extra items"
    ROW_DPS__COMMON_STOCK_PRIMARY_ISSUE = "DPS - common stock primary issue"
    ROW_GROSS_DIVIDEND__COMMON_STOCK = "Gross dividend - common stock"
    ROW_PRO_FORMA_NET_INCOME = "Pro forma net income"
    ROW_INTEREST_EXPENSE_SUPPLEMENTAL = "Interest expense, supplemental"
    ROW_DEPRECIATION_SUPPLEMENTAL = "Depreciation, supplemental"
    ROW_TOTAL_SPECIAL_ITEMS = "Total special items"
    ROW_NORMALIZED_INCOME_BEFORE_TAXES = "Normalized income before taxes"
    ROW_EFFECT_OF_SPECIAL_ITEMS_ON_INCOME_TAXES = "Effect of special items on income taxes"
    ROW_INCOME_TAX_EXCLUDING_IMPACT_OF_SPECIAL_ITEMS = "Income tax excluding impact of special items"
    ROW_NORMALIZED_INCOME_AFTER_TAX = "Normalized income after tax"
    ROW_NORMALIZED_INCOME_AVAIL_TO_COMMON = "Normalized income avail. to common"
    ROW_BASIC_NORMALIZED_EPS = "Basic normalized EPS"
    ROW_DILUTED_NORMALIZED_EPS = "Diluted normalized EPS"


class IC_BALANCE_DATA:
    BALANCE_DATA_FRAME_INDEX = 0
    NEW_BALANCE_LINE_ITEM_COLUMN_NAME = 'Balance Line Item'

    # DATA ROWS
    ROW_CASH_AND_SHORT_TERM_INVESTMENTS = "Cash And Short Term Investments"
    ROW_TOTAL_RECEIVABLES_NET = "Total Receivables, Net"
    ROW_TOTAL_INVENTORY = "Total Inventory"
    ROW_PREPAID_EXPENSES = "Prepaid expenses"
    ROW_OTHER_CURRENT_ASSETS_TOTAL = "Other current assets, total"
    ROW_TOTAL_CURRENT_ASSETS = "Total current assets"
    ROW_PROPERTY_PLANT_AND_EQUIPMENT_NET = "Property, plant & equipment, net"
    ROW_GOODWILL_NET = "Goodwill, net"
    ROW_INTANGIBLES_NET = "Intangibles, net"
    ROW_LONG_TERM_INVESTMENTS = "Long term investments"
    ROW_NOTE_RECEIVABLE__LONG_TERM = "Note receivable - long term"
    ROW_OTHER_LONG_TERM_ASSETS = "Other long term assets"
    ROW_TOTAL_ASSETS = "Total assets"
    ROW_ACCOUNTS_PAYABLE = "Accounts payable"
    ROW_ACCRUED_EXPENSES = "Accrued expenses"
    ROW_NOTES_PAYABLE_SHORTTERM_DEBT = "Notes payable/short-term debt"
    ROW_CURRENT_PORTION_LONGTERM_DEBT_CAPITAL_LEASES = "Current portion long-term debt/capital leases"
    ROW_OTHER_CURRENT_LIABILITIES_TOTAL = "Other current liabilities, total"
    ROW_TOTAL_CURRENT_LIABILITIES = "Total current liabilities"
    ROW_TOTAL_LONG_TERM_DEBT = "Total long term debt"
    ROW_TOTAL_DEBT = "Total debt"
    ROW_DEFERRED_INCOME_TAX = "Deferred income tax"
    ROW_MINORITY_INTEREST = "Minority interest"
    ROW_OTHER_LIABILITIES_TOTAL = "Other liabilities, total"
    ROW_TOTAL_LIABILITIES = "Total liabilities"
    ROW_COMMON_STOCK = "Common stock"
    ROW_ADDITIONAL_PAIDIN_CAPITAL = "Additional paid-in capital"
    ROW_RETAINED_EARNINGS__ACCUMULATED_DEFICIT_ = "Retained earnings (accumulated deficit)"
    ROW_TREASURY_STOCK__COMMON = "Treasury stock - common"
    ROW_UNREALIZED_GAIN__LOSS_ = "Unrealized gain (loss)"
    ROW_OTHER_EQUITY_TOTAL = "Other equity, total"
    ROW_TOTAL_EQUITY = "Total equity"
    ROW_TOTAL_LIABILITIES_AND_SHAREHOLDERS_EQUITY = "Total liabilities & shareholders' equity"
    ROW_TOTAL_COMMON_SHARES_OUTSTANDING = "Total common shares outstanding"
    ROW_TREASURY_SHARES__COMMON_PRIMARY_ISSUE = "Treasury shares - common primary issue"
