import re
import pandas
from datetime import datetime
from account import Account,AccountType
from transaction import FinancialTransaction, TransactionType
import compute_next_business_day


def get_account_from_key(key, request):
    account = Account(key)

    if account.account_type == AccountType.DEBIT_CARD:
        id_parts = key.split("_")
        associated_id = request.form[f"debitCard_association_{id_parts[1]}"]
        account.setAssociation(associated_id)
    elif account.account_type in [AccountType.CHECKING_ACCOUNT, AccountType.PREPAID_CARD]:
        bank = request.form[f"{key}_bank"]
        account.setBank(bank)

    return account

def get_dataset(account, file_path, config, associated_bank=None):

    if account.account_type == AccountType.PAYPAL:
        if config["PayPal"]['file_extension'] == "csv":
            read_params = {"filepath_or_buffer": file_path}
        elif config["PayPal"]['file_extension'] == "xlsx":
            read_params = {"io": file_path}
        read_params.update(config["PayPal"]['pandas_read_params'])
    else:
        bank = associated_bank or account.bank
        if config[bank][account.account_type.value]['file_extension'] == "csv":
            read_params = {"filepath_or_buffer": file_path}
        elif config[bank][account.account_type.value]['file_extension'] == "xlsx":
            read_params = {"io": file_path}
        read_params.update(config[bank][account.account_type.value]['pandas_read_params'])

    if account.account_type == AccountType.PAYPAL:
        if config["PayPal"]['file_extension'] == "csv":
            df = pandas.read_csv(**read_params)
        elif config["PayPal"]['file_extension'] == "xlsx":
            df = pandas.read_excel(**read_params)
    else:
        if config[bank][account.account_type.value]['file_extension'] == "csv":
            df = pandas.read_csv(**read_params)
        elif config[bank][account.account_type.value]['file_extension'] == "xlsx":
            df = pandas.read_excel(**read_params)

    return df

def get_normalization_function(account, config, normalization, associated_bank=None):
    if account.account_type == AccountType.PAYPAL:
        norm_fn_name = config["PayPal"].get('normalizationFunction')
    else:
        bank = associated_bank or account.bank
        norm_fn_name = config[bank][account.account_type.value].get('normalizationFunction')

    return getattr(normalization, norm_fn_name) if norm_fn_name else None

def process_dataframe(df, normalization_fn):
    if normalization_fn:
        normalization_fn(df)
    df["Found"] = False
    return df

def read_previous_transactions(csvFileSession):
    transactions = []

    for lineSession in csvFileSession.itertuples():

        if lineSession[2] == "withdrawal":
            transactionType = TransactionType.WITHDRAWAL
        elif lineSession[2] == "deposit":
            transactionType = TransactionType.DEPOSIT
        else:
            transactionType = TransactionType.TRANSFER

        date = datetime.strptime(lineSession[1], '%Y-%m-%dT%H:%M')

        financialTransaction = FinancialTransaction(transactionType, date, "EUR", lineSession[6], lineSession[3], lineSession[4])

        if not pandas.isna(lineSession[5]):
            financialTransaction.setDescription(lineSession[5])
        
        if not pandas.isna(lineSession[7]):
            financialTransaction.setCategoryID(lineSession[7])

        transactions.append(financialTransaction)
    
    return transactions    

def compare_accounts(accounts, relationships, config):

    transactions = []
    index_dict = 0

    for relationship in relationships:
        print(accounts.get(relationship[0]).account_type.value+" "+accounts.get(relationship[1]).account_type.value)
        a1 = accounts.get(relationship[0])
        a2 = accounts.get(relationship[1])
        if a1.account_type ==  AccountType.PAYPAL:
            fields_a1 = config.get("PayPal").get('fields')
            bank_a1 = "PayPal"
        elif a1.account_type ==  AccountType.DEBIT_CARD:
            fields_a1 = config.get(accounts.get(a1.id_associated_account).bank).get(a1.account_type.value).get('fields')
            bank_a1 = accounts.get(a1.id_associated_account).bank
        else:
            fields_a1 = config.get(a1.bank).get(a1.account_type.value).get('fields')
            bank_a1 = a1.bank
        fields_a2 = config.get(a2.bank).get(a2.account_type.value).get('fields')


        indexesToDrop_a1 = []
        indexesToDrop_a2 = []
        for transaction_a1 in a1.dataframe.itertuples():
            found = False
            amount_a1 = transaction_a1[fields_a1.get('amount')]
            date_a1 = transaction_a1[fields_a1.get('date')]
            destination_a1 = transaction_a1[fields_a1.get('destination')]
            if fields_a1.get('time'):
                time_a1 = transaction_a1[fields_a1.get('time')]
            if fields_a1.get('source'):
                source_a1 = transaction_a1[fields_a1.get('source')]

            for transaction_a2 in a2.dataframe.itertuples():
                if transaction_a2[a2.dataframe.columns.get_loc("Found")+1] == False:
                    amount_a2 = transaction_a2[fields_a2.get('amount')]
                    date_a2 = transaction_a2[fields_a2.get('date')]
                    destination_a2 = transaction_a2[fields_a2.get('destination')]
                    if fields_a2.get('time'):
                        time_a2 = transaction_a2[fields_a2.get('time')]
                    if fields_a2.get('source'):
                        source_a2 = transaction_a2[fields_a2.get('source')]

                    for daysNumber in relationship[2]:
                        #if (date_a1 > datetime(2024, 1, 2) and date_a1 < datetime(2024, 1, 4)) and (date_a2 > datetime(2024, 1, 5) and date_a2 < datetime(2024, 1, 7)):
                            #print("transaction_a1: "+str(transaction_a1))
                            #print("transaction_a2: "+str(transaction_a2))
                            #print("daysNumber: "+str(daysNumber))
                            #print(compute_next_business_day.next_number_business_day(date_a1.to_pydatetime(), 'IT', daysNumber))
                        if abs(amount_a1) == abs(amount_a2) and compute_next_business_day.next_number_business_day(date_a1.to_pydatetime(), 'IT', daysNumber) == date_a2.to_pydatetime():
                            
                            if (a1.account_type == AccountType.DEBIT_CARD and a2.account_type == AccountType.CHECKING_ACCOUNT) or (a1.account_type == AccountType.CHECKING_ACCOUNT and a2.account_type == AccountType.DEBIT_CARD):
                                descPartsA1 = re.split(r'\s{2,}', destination_a1)
                                descPartsA2 = re.split(r'\s{2,}', destination_a2)

                                if (descPartsA1[0] == descPartsA2[3]) or (descPartsA1[0] == descPartsA2[4]):
                                    if amount_a1 > 0:
                                        transactionType = TransactionType.DEPOSIT
                                        sourceAccount = descPartsA1[0]
                                        destinationAccount = bank_a1
                                    else:
                                        transactionType = TransactionType.WITHDRAWAL
                                        destinationAccount = descPartsA1[0]
                                        sourceAccount = bank_a1

                                    if time_a1:
                                        date_a1 = date_a1.replace(hour=time_a1.hour, minute=time_a1.minute)
                                    elif time_a2:
                                        date_a1 = date_a1.replace(hour=time_a2.hour, minute=time_a2.minute)
                                    
                                    transaction = FinancialTransaction(
                                        transaction_type=transactionType,
                                        date=date_a1,
                                        currency_code="EUR",
                                        amount=abs(amount_a1),
                                        source_account=sourceAccount,
                                        destination_account=destinationAccount
                                    )

                                    transactions.append(transaction)
                                    index_dict += 1

                                    indexesToDrop_a1.append(transaction_a1[0])
                                    indexesToDrop_a2.append(transaction_a2[0])
                                    found = True
                                    a1.dataframe.at[transaction_a1[0], "Found"] = True
                                    a2.dataframe.at[transaction_a2[0], "Found"] = True
                            
                            elif (a1.account_type in [AccountType.DEBIT_CARD, AccountType.CHECKING_ACCOUNT, AccountType.PREPAID_CARD] and a2.account_type == AccountType.PAYPAL) or (a1.account_type == AccountType.PAYPAL and a2.account_type in [AccountType.DEBIT_CARD, AccountType.CHECKING_ACCOUNT, AccountType.PREPAID_CARD]):
                                if a1.account_type == AccountType.PAYPAL:
                                    source = source_a1
                                    destination = destination_a1
                                    bank_secondAccount = accounts.get(a2.id_associated_account).bank if a2.account_type == AccountType.DEBIT_CARD else a2.bank
                                    date = date_a1.replace(hour=time_a1.hour, minute=time_a1.minute)
                                elif a2.account_type == AccountType.PAYPAL:
                                    source = source_a2
                                    destination = destination_a2
                                    bank_secondAccount = accounts.get(a1.id_associated_account).bank if a1.account_type == AccountType.DEBIT_CARD else a1.bank
                                    date = date_a2.replace(hour=time_a2.hour, minute=time_a2.minute)


                                if source.lower().find(bank_secondAccount.lower()) > -1:
                                    if amount_a1 > 0:
                                        transactionType = TransactionType.DEPOSIT
                                        sourceAccount = destination
                                        destinationAccount = bank_secondAccount
                                    else:
                                        transactionType = TransactionType.WITHDRAWAL
                                        destinationAccount = destination
                                        sourceAccount = bank_secondAccount

                                    transaction = FinancialTransaction(
                                        transaction_type=transactionType,
                                        date=date,
                                        currency_code="EUR",
                                        amount=abs(amount_a1),
                                        source_account=sourceAccount,
                                        destination_account=destinationAccount
                                    )

                                    transactions.append(transaction)
                                    index_dict += 1

                                    found = True
                                    indexesToDrop_a1.append(transaction_a1[0])
                                    indexesToDrop_a2.append(transaction_a2[0])
                                    a1.dataframe.at[transaction_a1[0], "Found"] = True
                                    a2.dataframe.at[transaction_a2[0], "Found"] = True

                                    break
                    if found:
                        break
    
    return transactions

def elaborate_checking_account_unicredit(account, config):
    transactions = []
    fields_account = config.get(account.bank).get(account.account_type.value).get('fields')

    for transaction_account in account.dataframe.itertuples():
        amount_account = transaction_account[fields_account.get('amount')]
        date_account = transaction_account[fields_account.get('date')]
        destination_account = transaction_account[fields_account.get('destination')]

        descPartsBank = re.split(r'\s{2,}', destination_account)

        if transaction_account[account.dataframe.columns.get_loc("Found")+1] == False:

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
                #print(lineBank)
                continue
    return transactions

def elaborate_paypal(account, config):
    transactions = []
    fields_account = config.get("PayPal").get('fields')

    for transaction_account in account.dataframe.itertuples():
        amount_account = transaction_account[fields_account.get('amount')]
        date_account = transaction_account[fields_account.get('date')]
        destination_account = transaction_account[fields_account.get('destination')]
        time_account = transaction_account[fields_account.get('time')]
        source_account = transaction_account[fields_account.get('source')]

        date_account = date_account.replace(hour=time_account.hour, minute=time_account.minute)

        if transaction_account[account.dataframe.columns.get_loc("Found")+1] == False:

            if amount_account > 0:
                transactionType = TransactionType.DEPOSIT
                sourceAccount = destination_account
                destinationAccount = source_account
            else:
                transactionType = TransactionType.WITHDRAWAL
                destinationAccount = destination_account
                sourceAccount = source_account


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

def elaborate_prepaid_card_postepay(account, config):
    transactions = []
    fields_account = config.get(account.bank).get(account.account_type.value).get('fields')

    for transaction_account in account.dataframe.itertuples():
        amount_account = transaction_account[fields_account.get('amount')]
        date_account = transaction_account[fields_account.get('date')]
        destination_account = transaction_account[fields_account.get('destination')]
        time_account = transaction_account[fields_account.get('time')]

        date_account = date_account.replace(hour=time_account.hour, minute=time_account.minute)

        if transaction_account[account.dataframe.columns.get_loc("Found")+1] == False:

            if "PAGAMENTO ON LINE" in destination_account or "PAGAMENTO POS ESERCENTE" in destination_account or "PAGAMENTO PAGA" in destination_account:
                regex = r"[0-9]{2}\/[0-9]{2}\/[0-9]{4}\s[0-9]{2}\.[0-9]{2}"

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

def findSourceDestinationCategoryID(transactions, fireflyIII):
    list_transactions = []
    for transaction in transactions:
        sourceAccount = transaction.source_account
        #if pandas.isna(sourceAccount):
            #sourceAccount = ""
        sourceAccountsFirefly = fireflyIII.autocompleteAccounts(sourceAccount, "Revenue account")
        if len(sourceAccountsFirefly) > 0:
            transaction.setSourceAccountID(sourceAccountsFirefly[0].get('id'))
        
        destinationAccount = transaction.destination_account
        #if pandas.isna(destinationAccount):
        #    destinationAccount = ""
        destinationAccountsFirefly = fireflyIII.autocompleteAccounts(destinationAccount, "Expense account")
        if len(destinationAccountsFirefly) > 0:
            transaction.setDestinationAccountID(destinationAccountsFirefly[0].get('id'))

        if not hasattr(transaction, 'category_id'):
            accountCounterpartyID = transaction.getCounterpartyAccount().get('id')
            if accountCounterpartyID is not None:
                accountTransactions = fireflyIII.getTransactionsOfAccount(accountCounterpartyID)
                transaction.setCategoryID(getMostUsedCategoryID(accountTransactions))
        
        list_transactions.append(transaction)
    
    return list_transactions

def getMostUsedCategoryID(accountTransaction):

    categories = {}
    if "data" in accountTransaction:
        for singleData in accountTransaction.get('data'):
            for transaction in singleData.get('attributes').get('transactions'):
                category_id = transaction.get('category_id')
                if category_id in categories:
                    categories.update({category_id: categories[category_id]+1})
                else:
                    categories.update({category_id: 1})
    if len(categories) > 0:
        return max(categories, key=categories.get)
    else:
        return -1

def checkExistingTransations(sourceTransations, fireflyIII):
    transactionsSorted = sorted(sourceTransations, key=lambda x: (x.date, x.amount))

    transactionsNotExistend = []
    i = 0
    j = 0

    while j < len(transactionsSorted):
        fireflyAssetId = transactionsSorted[j].getBankAccount().get("id")
        if fireflyAssetId == None:
            fireflyAssetId = 1
        query = "account_id:"+fireflyAssetId+" amount:"+('{:.2f}'.format(transactionsSorted[j].amount))+" date_on:"+transactionsSorted[j].date.strftime('%Y-%m-%d')
        
        goNext = True
        k = j + 1
        n = 1
        
        if (k != len(transactionsSorted)):
            while(goNext):
                if (transactionsSorted[j].amount == transactionsSorted[k].amount) and (transactionsSorted[j].date.strftime('%Y-%m-%d') == transactionsSorted[k].date.strftime('%Y-%m-%d')):
                    n += 1
                    goNext = True
                else:
                    goNext = False
                if (k != len(transactionsSorted) - 1):
                    k += 1
        
        
        result = fireflyIII.searchTransations(query)

        if len(result["data"]) != n:
            query = "account_id:"+fireflyAssetId+" amount:"+('{:.2f}'.format(transactionsSorted[j].amount * n))+" date_on:"+transactionsSorted[j].date.strftime('%Y-%m-%d')

            result = fireflyIII.searchTransations(query)

            if len(result["data"]) != 1:
                for z in range(j, j+n):
                    transactionsNotExistend.append(transactionsSorted[z])

        j += n
    return transactionsNotExistend