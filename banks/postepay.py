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
from datetime import datetime
from dateutil import parser
from entities.transaction import FinancialTransaction, TransactionType

def normalizePostePay(csvPostePay):
    regex = r"[0-9]{2}\/[0-9]{2}\/[0-9]{4}\s+[0-9]{2}[\.\:][0-9]{2}"
    for row in csvPostePay.itertuples():
        desc = row[4]
        finds = re.findall(regex, desc)
        if len(finds) > 0:
            date_object = parser.parse(finds[0].replace('.', ':'))
            csvPostePay.at[row[0], "Time"] = date_object
        else:
            csvPostePay.at[row[0], "Time"] = datetime.now().replace(hour=0, minute=0)

def elaborate_prepaid_card_postepay(account, config):
    transactions = []
    fields_account = config.get(account.bank).get(account.account_type.value).get('fields')
    for transaction_account in account.dataframe.itertuples():
        amount_account = transaction_account[fields_account.get('amount')]
        date_account = transaction_account[fields_account.get('date')]
        destination_account = transaction_account[fields_account.get('destination')]
        time_account = transaction_account[fields_account.get('time')]
        date_account = date_account.replace(hour=time_account.hour, minute=time_account.minute)
        found_index = None
        try:
            found_index = account.dataframe.columns.get_loc("Found")
            is_found = transaction_account[found_index + 1]
        except (KeyError, IndexError):
            is_found = False
        if is_found == False:
            if "PAGAMENTO ON LINE" in destination_account or "PAGAMENTO POS ESERCENTE" in destination_account or "PAGAMENTO PAGA" in destination_account:
                regex = r"[0-9]{2}\/[0-9]{2}\/[0-9]{4}\s[0-9]{2}\.[0-9]{2}"
                try:
                    split = re.split(regex, destination_account)
                except re.error as e:
                    print(f"Warning: Invalid regex pattern: {e}")
                    split = [destination_account]
                transaction = FinancialTransaction(
                    transaction_type=TransactionType.WITHDRAWAL,
                    date=date_account,
                    currency_code="EUR",
                    amount=abs(amount_account),
                    source_account="PostePay",
                    destination_account=split[1].strip()
                )
                transactions.append(transaction)
                account.dataframe.at[transaction_account[0], "Found"] = True
            elif "PAGAMENTO ONLINE" in destination_account:
                regex = r"PAGAMENTO ONLINE"
                split = re.split(regex, destination_account)
                transaction = FinancialTransaction(
                    transaction_type=TransactionType.WITHDRAWAL,
                    date=date_account,
                    currency_code="EUR",
                    amount=abs(amount_account),
                    source_account="PostePay",
                    destination_account=split[1].strip()
                )
                transactions.append(transaction)
                account.dataframe.at[transaction_account[0], "Found"] = True
            elif "COMMISSIONI" in destination_account:
                transaction = FinancialTransaction(
                    transaction_type=TransactionType.WITHDRAWAL,
                    date=date_account,
                    currency_code="EUR",
                    amount=abs(amount_account),
                    source_account="PostePay",
                    destination_account=destination_account
                )
                transactions.append(transaction)
                account.dataframe.at[transaction_account[0], "Found"] = True
            elif "Ricarica Postepay" in destination_account or "RICARICA CARTA" in destination_account:
                regex = r"Ricarica Postepay DA|Ricarica effettuata da"
                split = re.split(regex, destination_account)
                if len(split) > 1:
                    source = split[1].strip()
                else:
                    source = split[0].strip()
                transaction = FinancialTransaction(
                    transaction_type=TransactionType.DEPOSIT,
                    date=date_account,
                    currency_code="EUR",
                    amount=abs(amount_account),
                    source_account=source,
                    destination_account="PostePay"
                )
                transactions.append(transaction)
                account.dataframe.at[transaction_account[0], "Found"] = True
            elif "RICARICA PRESSO ESERCENTE" in destination_account:
                transaction = FinancialTransaction(
                    transaction_type=TransactionType.DEPOSIT,
                    date=date_account,
                    currency_code="EUR",
                    amount=abs(amount_account),
                    source_account=destination_account,
                    destination_account="PostePay"
                )
                transactions.append(transaction)
                account.dataframe.at[transaction_account[0], "Found"] = True
    return transactions
