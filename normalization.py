from datetime import timedelta, datetime
from dateutil import parser
import pandas
import re
from banks.paypal import normalizePayPal
from banks.postepay import normalizePostePay

def normalizeBank(csvBank):
    """Normalize bank CSV data by converting amount format.
    
    Converts amount values from European format (e.g., "1.234,56") to
    float format by removing thousand separators and converting comma
    to decimal point.
    
    Args:
        csvBank (pandas.DataFrame): DataFrame containing bank transaction data
                                  with 'Importo (EUR)' column in European format.
    """
    for lineBank in csvBank.itertuples():
        csvBank.at[lineBank[0], 'Importo (EUR)'] = float(lineBank[4].replace('.', '').replace(',', '.'))

