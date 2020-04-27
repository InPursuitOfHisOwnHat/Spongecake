import logging as log
import requests as rq
import pandas as pd


class FinancialWebsiteInterface:

    @staticmethod
    def extract_tables_from_raw_html(data):
        tables = []
        # Get first table tag position
        table_tag_start_pos = data.find('<table')

        while table_tag_start_pos != -1:
            table_tag_end_pos = data.find('</table>', table_tag_start_pos)
            tables.append(data[table_tag_start_pos:table_tag_end_pos + len('</table>')])
            table_tag_start_pos = table_tag_start_pos = data.find('<table', table_tag_end_pos+len('</table>'))
        log.info('Returning [{0}] tables found in html data'.format(len(tables)))
        return tables

    @staticmethod
    def download_web_page(url):
        log.info('Attempting to download from following url: {0}'.format(url))
        http_result = rq.get(url)
        if http_result.status_code != 200:
            log.error('Received HTTP response code {0} when trying to call {1}. Returning nothing.')
            log.error(http_result.text)
            return ''

        if http_result.url != url:
            log.warning('Unexpectedly re-directed when trying to call {0}. Sent to {1} instead.'.format(url, http_result.url))

        return http_result.text

    @staticmethod
    def get_dataframes_from_html_tables(html_tables, headers=0):
        # Build DataFrame list from tables
        income_dataframes = []
        for html_table in html_tables:
            income_dataframe = pd.read_html(html_table, header=headers)
            if len(income_dataframe) > 0:
                # The read_html() function returns a list, but we know only one table will be returned for each item in the html_tables list,
                # so we just take the head of the returned list
                income_dataframes.append(income_dataframe[0])
            else:
                log.error('No tables were found in current iteration')
        return income_dataframes
