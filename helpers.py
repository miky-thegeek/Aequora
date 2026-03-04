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
"""Helper functions for form processing, data transformation, and account relationships."""
from collections import defaultdict
import pandas
import base_v2
from entities.account import AccountType


def generate_dynamic_relationship(accounts):
    """Generate relationships between accounts based on their types.
    
    Creates relationship rules between different account types (debit cards,
    checking accounts, PayPal, prepaid cards) with specific day offsets
    for transaction matching.
    
    Args:
        accounts (list): List of Account objects to generate relationships for.
        
    Returns:
        list: List of tuples containing (account1_id, account2_id, [day_offsets])
              representing valid relationships between accounts.
    """
    relazioni = []

    for a1 in accounts:
        for a2 in accounts:
            if a1.id == a2.id:
                continue

            t1 = a1.account_type
            t2 = a2.account_type

            # Regola 1: debito → solo con conto associato
            if t1 == AccountType.DEBIT_CARD and t2 == AccountType.CHECKING_ACCOUNT and a1.id_associated_account == a2.id:
                relazioni.append((a1.id, a2.id, [0]))

            # Regola 2: paypal → conto
            elif t1 == AccountType.PAYPAL and t2 == AccountType.CHECKING_ACCOUNT:
                relazioni.append((a1.id, a2.id, [0, 1, 2, 3]))

            # Regola 3: paypal → prepagata
            elif t1 == AccountType.PAYPAL and t2 == AccountType.PREPAID_CARD:
                relazioni.append((a1.id, a2.id, [-1, 0, 1]))

            # Regola 4: prepagata → conto
            elif t1 == AccountType.PREPAID_CARD and t2 == AccountType.CHECKING_ACCOUNT:
                relazioni.append((a1.id, a2.id, [1]))
            
            # Regola 5: conto → conto (es. trasferimenti tra conti)
            elif t1 == AccountType.CHECKING_ACCOUNT and t2 == AccountType.CHECKING_ACCOUNT and not any((r[0] == a1.id and r[1] == a2.id) or (r[0] == a2.id and r[1] == a1.id) for r in relazioni):
                relazioni.append((a1.id, a2.id, [0]))

            # Altri casi personalizzabili qui...
    
    return relazioni


def listToDict(transactions_list):
    """Convert a list of transactions to a dictionary with numeric keys.
    
    Args:
        transactions_list (list): List of FinancialTransaction objects.
        
    Returns:
        dict: Dictionary with integer keys (0, 1, 2, ...) mapping to
              transaction objects.
    """
    i = 0
    transactions_dict = {}
    for transaction in transactions_list:
        transactions_dict[i] = transaction
        i += 1
    return transactions_dict


# CSV field names constant
CSV_FIELDNAMES = ['date', 'transactionType', 'sourceAccount', 'destinationAccount', 'description', 'amount', 'category', 'sourceAccountId', 'destinationAccountId']


def parse_form_grouped(form_items):
    """Parse form items into grouped data structure.
    
    Parses form data with keys in format "prefix_suffix" into a dictionary
    grouped by suffix, where each suffix maps to a dict of prefix-value pairs.
    
    Args:
        form_items (dict): Dictionary of form field names and values,
                          e.g., {"date_0": "2024-01-01", "amount_0": "100"}.
        
    Returns:
        defaultdict: Dictionary grouped by suffix (e.g., "0") containing
                     prefix-value pairs (e.g., {"date": "2024-01-01", 
                     "amount": "100"}).
    """
    grouped_data = defaultdict(dict)
    for key, value in form_items.items():
        try:
            prefix, suffix = key.rsplit('_', 1)
            grouped_data[suffix][prefix] = value
        except ValueError:
            continue
    return grouped_data


def csv_rows_from_grouped(grouped_data):
    """Extract CSV rows from grouped data.
    
    Converts grouped data dictionary into a list of dictionaries suitable
    for CSV writing.
    
    Args:
        grouped_data (dict): Dictionary grouped by suffix, where each value
                            is a dict of field-value pairs.
        
    Returns:
        list: List of dictionaries, each representing a CSV row.
    """
    csv_rows = []
    for _, value in grouped_data.items():
        csv_rows.append(value)
    return csv_rows


def dataframe_from_grouped(grouped_data):
    """Convert grouped data to pandas DataFrame.
    
    Converts grouped form data into a pandas DataFrame with standardized
    column names. Empty category values are converted to pandas.NA.
    
    Args:
        grouped_data (dict): Dictionary grouped by suffix, where each value
                            is a dict of field-value pairs.
        
    Returns:
        pandas.DataFrame: DataFrame with columns matching CSV_FIELDNAMES,
                         with empty category strings replaced by pandas.NA.
    """
    normalized_rows = []
    for _, row in grouped_data.items():
        normalized = {k: row.get(k) for k in CSV_FIELDNAMES}
        normalized_rows.append(normalized)
    df = pandas.DataFrame(normalized_rows, columns=CSV_FIELDNAMES)
    # Ensure empty category is treated as missing so downstream logic skips it
    if 'category' in df.columns:
        df['category'] = df['category'].replace('', pandas.NA)
    return df


def build_transactions_context_from_df(df, fireflyIII):
    """Build transactions context from DataFrame for rendering.
    
    Processes a DataFrame of transactions by reading them, enriching with
    category and account IDs, checking for duplicates, and preparing
    the context for template rendering.
    
    Args:
        df (pandas.DataFrame): DataFrame containing transaction data with
                              columns matching CSV_FIELDNAMES.
        fireflyIII (FireflyIII): FireflyIII client instance for API calls.
        
    Returns:
        tuple: A tuple containing:
            - dict: Dictionary of transactions with integer keys
            - dict: Categories dictionary from FireflyIII API
    """
    transactions = base_v2.read_previous_transactions(df)
    transactions = base_v2.findSourceDestinationCategoryID(transactions, fireflyIII)
    transactions_not_existing = base_v2.checkExistingTransations(transactions, fireflyIII)
    transactions_dict = listToDict(transactions_not_existing)
    categories = fireflyIII.getCategories()
    return transactions_dict, categories

