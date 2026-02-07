# This file is part of Aequora.
#
# Aequora is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Aequora is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Aequora.  If not, see <https://www.gnu.org/licenses/>.
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

