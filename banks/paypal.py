from datetime import timedelta
import pandas
from entities.transaction import FinancialTransaction, TransactionType

def normalizePayPal(csvPayPal):
    print("Normalizing PayPal CSV data...")
    pagamenti = csvPayPal.copy()
    addebiti = csvPayPal[csvPayPal['Descrizione'].str.contains('Bonifico|Versamento generico con carta|Pagamento con credito acquirenti PayPal|Trasferimento avviato dall\'utente|Prelievo|Blocco conto per autorizzazione aperta|Storno di blocco conto generico')]
    for index, pagamento in addebiti.iterrows():
        pagamenti.drop(index, inplace=True)
    indexes_to_drop = []
    for index, pagamento in pagamenti.iterrows():
        importo = pagamento.iloc[5]
        valuta = pagamento.iloc[4]
        data = pagamento.iloc[0]
        addebito_match = addebiti[
            (addebiti['Valuta'] == valuta) &
            (abs(addebiti['Lordo ']) == abs(importo)) &
            ((addebiti['Data'] == data) | (addebiti['Data'] == data + timedelta(days=1)) )
        ].index
        if len(addebito_match.to_list()) > 0:
            for index_addebiti in addebito_match.to_list():
                bank = csvPayPal.iat[index_addebiti, 12]
                if pandas.isna(bank):
                    csvPayPal.iat[index, 12] = "PayPal"
                else:
                    csvPayPal.iat[index, 12] = bank
        else:
            csvPayPal.iat[index, 12] = "PayPal"
        indexes_to_drop.extend(addebito_match.to_list())
    if len(indexes_to_drop) > 0:
        csvPayPal.drop(csvPayPal.index[indexes_to_drop], inplace=True)

def elaborate_paypal(account, config):
    print("Elaborating PayPal transactions...")
    transactions = []
    fields_account = config.get("PayPal", {}).get('fields')
    if not fields_account:
        print("Warning: Missing PayPal fields configuration")
        return transactions
    for transaction_account in account.dataframe.itertuples():
        amount_account = transaction_account[fields_account.get('amount')]
        date_account = transaction_account[fields_account.get('date')]
        destination_account = transaction_account[fields_account.get('destination')]
        time_account = transaction_account[fields_account.get('time')]
        source_account = transaction_account[fields_account.get('source')]
        try:
            if hasattr(time_account, 'hour') and hasattr(time_account, 'minute'):
                date_account = date_account.replace(hour=time_account.hour, minute=time_account.minute)
            elif isinstance(time_account, str):
                from datetime import datetime
                time_obj = datetime.strptime(time_account, '%H:%M')
                date_account = date_account.replace(hour=time_obj.hour, minute=time_obj.minute)
        except (AttributeError, ValueError) as e:
            print(f"Warning: Could not process time for transaction: {e}")
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
                destinationAccount = source_account
                if pandas.isna(destinationAccount) or destinationAccount.strip() == "":
                    destinationAccount = "PayPal"
            else:
                transactionType = TransactionType.WITHDRAWAL
                destinationAccount = destination_account
                sourceAccount = source_account
                if pandas.isna(sourceAccount) or sourceAccount.strip() == "":
                    sourceAccount = "PayPal"
            #print(f"Creating transaction PayPal: {transactionType} of {abs(amount_account)} EUR on {date_account} from {sourceAccount} to {destinationAccount}")
            transaction = FinancialTransaction(
                transaction_type=transactionType,
                date=date_account,
                currency_code="EUR",
                amount=abs(amount_account),
                source_account=sourceAccount,
                destination_account=destinationAccount
            )
            transactions.append(transaction)
            account.dataframe.at[transaction_account[0], "Found"] = True
    return transactions
