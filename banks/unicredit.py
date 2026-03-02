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
import re
from entities.transaction import FinancialTransaction, TransactionType

def elaborate_checking_account_unicredit(account, config):
    print("Elaborating Unicredit checking account transactions...")
    transactions = []
    fields_account = config.get(account.bank).get(account.account_type.value).get('fields')
    for transaction_account in account.dataframe.itertuples():
        amount_account = transaction_account[fields_account.get('amount')]
        date_account = transaction_account[fields_account.get('date')]
        destination_account = transaction_account[fields_account.get('destination')]
        descPartsBank = re.split(r'\s{2,}', destination_account)
        found_index = None
        try:
            found_index = account.dataframe.columns.get_loc("Found")
            is_found = transaction_account[found_index + 1]
        except (KeyError, IndexError):
            is_found = False
        if is_found == False:
            if "VOSTRI EMOLUMENTI" in destination_account:
                transaction = FinancialTransaction(
                    transaction_type=TransactionType.DEPOSIT,
                    date=date_account.to_pydatetime(),
                    currency_code="EUR",
                    amount=amount_account,
                    source_account=descPartsBank[2],
                    destination_account="Unicredit"
                )
                transaction.setDescription(descPartsBank[3]+descPartsBank[4])
                transactions.append(transaction)
                account.dataframe.at[transaction_account[0], "Found"] = True
            elif "ADDEBITO SEPA DD" in destination_account.upper():
                transaction = FinancialTransaction(
                    transaction_type=TransactionType.WITHDRAWAL,
                    date=date_account.to_pydatetime(),
                    currency_code="EUR",
                    amount=abs(amount_account),
                    source_account="Unicredit",
                    destination_account=descPartsBank[3]
                )
                transactions.append(transaction)
                account.dataframe.at[transaction_account[0], "Found"] = True
            elif "PRELIEVO" in destination_account.upper():
                transaction = FinancialTransaction(
                    transaction_type=TransactionType.TRANSFER,
                    date=date_account.to_pydatetime(),
                    currency_code="EUR",
                    amount=abs(amount_account),
                    source_account="Unicredit",
                    destination_account="Contanti"
                )
                transactions.append(transaction)
                account.dataframe.at[transaction_account[0], "Found"] = True
            elif "BONIFICO A VOSTRO FAVORE" in destination_account.upper():
                if "BONIFICO SEPA" in descPartsBank[1]:
                    description = descPartsBank[3]+descPartsBank[4]
                else:
                    description = descPartsBank[1]
                transaction = FinancialTransaction(
                    transaction_type=TransactionType.DEPOSIT,
                    date=date_account.to_pydatetime(),
                    currency_code="EUR",
                    amount=abs(amount_account),
                    source_account=descPartsBank[2],
                    destination_account="Unicredit"
                )
                transaction.setDescription(description)
                transactions.append(transaction)
                account.dataframe.at[transaction_account[0], "Found"] = True
            elif "DISPOSIZIONE DI BONIFICO" in destination_account.upper():
                transaction = FinancialTransaction(
                    transaction_type=TransactionType.WITHDRAWAL,
                    date=date_account.to_pydatetime(),
                    currency_code="EUR",
                    amount=abs(amount_account),
                    source_account="Unicredit",
                    destination_account=descPartsBank[2]
                )
                transaction.setDescription(descPartsBank[3])
                transactions.append(transaction)
                account.dataframe.at[transaction_account[0], "Found"] = True
            elif "DISPOSIZIONE DI ADDEBITO" in destination_account.upper():
                transaction = FinancialTransaction(
                    transaction_type=TransactionType.WITHDRAWAL,
                    date=date_account.to_pydatetime(),
                    currency_code="EUR",
                    amount=abs(amount_account),
                    source_account="Unicredit",
                    destination_account=descPartsBank[1]
                )
                transactions.append(transaction)
                account.dataframe.at[transaction_account[0], "Found"] = True
            elif "COMMISSIONI - PROVVIGIONI - SPESE" in destination_account.upper():
                transaction = FinancialTransaction(
                    transaction_type=TransactionType.WITHDRAWAL,
                    date=date_account.to_pydatetime(),
                    currency_code="EUR",
                    amount=abs(amount_account),
                    source_account="Unicredit",
                    destination_account="Banca Unicredit"
                )
                transaction.setDescription(descPartsBank[1])
                transactions.append(transaction)
                account.dataframe.at[transaction_account[0], "Found"] = True
            elif "IMPOSTA BOLLO" in destination_account.upper():
                transaction = FinancialTransaction(
                    transaction_type=TransactionType.WITHDRAWAL,
                    date=date_account.to_pydatetime(),
                    currency_code="EUR",
                    amount=abs(amount_account),
                    source_account="Unicredit",
                    destination_account="Banca Unicredit"
                )
                transaction.setDescription(descPartsBank[0])
                transactions.append(transaction)
                account.dataframe.at[transaction_account[0], "Found"] = True
            elif "CARTA *3455" in destination_account.upper():
                transaction = FinancialTransaction(
                    transaction_type=TransactionType.WITHDRAWAL,
                    date=date_account.to_pydatetime(),
                    currency_code="EUR",
                    amount=abs(amount_account),
                    source_account="Unicredit",
                    destination_account=descPartsBank[4]
                )
                transactions.append(transaction)
                account.dataframe.at[transaction_account[0], "Found"] = True
            elif "VERSAMENTO" in destination_account.upper():
                transaction = FinancialTransaction(
                    transaction_type=TransactionType.DEPOSIT,
                    date=date_account.to_pydatetime(),
                    currency_code="EUR",
                    amount=abs(amount_account),
                    source_account="Risparmi",
                    destination_account="Unicredit"
                )
                transactions.append(transaction)
                account.dataframe.at[transaction_account[0], "Found"] = True
            elif "ACCREDITI VARI" in destination_account.upper():
                transaction = FinancialTransaction(
                    transaction_type=TransactionType.DEPOSIT,
                    date=date_account.to_pydatetime(),
                    currency_code="EUR",
                    amount=abs(amount_account),
                    source_account="Banca Unicredit",
                    destination_account="Unicredit"
                )
                transaction.setDescription(descPartsBank[1])
                transactions.append(transaction)
                account.dataframe.at[transaction_account[0], "Found"] = True
            else:
                continue
    return transactions

def normalizeUnicredit(csvBank):
    """Normalize bank CSV data by converting amount format.
    
    Converts amount values from European format (e.g., "1.234,56") to
    float format by removing thousand separators and converting comma
    to decimal point.
    
    Args:
        csvBank (pandas.DataFrame): DataFrame containing bank transaction data
                                  with 'Importo (EUR)' column in European format.
    """
    print("Normalizing Unicredit CSV data...")
    csvBank["Importo (EUR)"] = (
    csvBank["Importo (EUR)"]
        .astype(str)
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False)
        .astype(float)
)