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
from entities.transaction import FinancialTransaction, TransactionType

def elaborate_checking_account_revolut_it(account, config):
    print("Elaborating Revolut Italia checking account transactions...")
    transactions = []
    fields_account = config.get(account.bank).get(account.account_type.value).get('fields')
    for transaction_account in account.dataframe.itertuples():
        amount_account = transaction_account[fields_account.get('amount')]
        date_account = transaction_account[fields_account.get('date')]
        destination_account = transaction_account[fields_account.get('destination')]

        found_index = None
        try:
            found_index = account.dataframe.columns.get_loc("Found")
            is_found = transaction_account[found_index + 1]
        except (KeyError, IndexError):
            is_found = False
        if is_found == False:
            if amount_account > 0:
                transactionType = TransactionType.DEPOSIT
                sourceAccount = destination_account
                destinationAccount = "Revolut"
            else:
                transactionType = TransactionType.WITHDRAWAL
                sourceAccount = "Revolut"
                destinationAccount = destination_account
            transaction = FinancialTransaction(
                transaction_type=transactionType,
                date=date_account.to_pydatetime(),
                currency_code="EUR",
                amount=abs(amount_account),
                source_account=sourceAccount,
                destination_account=destinationAccount
            )
            transactions.append(transaction)
            account.dataframe.at[transaction_account[0], "Found"] = True
    return transactions