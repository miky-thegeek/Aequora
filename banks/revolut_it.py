from entities.transaction import FinancialTransaction, TransactionType

def elaborate_checking_account_revolut_it(account, config):
    print("Elaborating Revolut Italia checking account transactions...")
    transactions = []
    fields_account = config.get(account.bank).get(account.account_type.value).get('fields')
    for transaction_account in account.dataframe.itertuples():
        amount_account = transaction_account[fields_account.get('amount')]
        print("Amount account:", amount_account)
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