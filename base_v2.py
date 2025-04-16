import re
import pandas
from account import AccountType
from transaction import FinancialTransaction, TransactionType
import compute_next_business_day



def compare_accounts(accounts, relationships, config):

    transactions = {}
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
        for transation_a1 in a1.dataframe.itertuples():
            found = False
            amount_a1 = transation_a1[fields_a1.get('amount')]
            date_a1 = transation_a1[fields_a1.get('date')]
            destination_a1 = transation_a1[fields_a1.get('destination')]
            if fields_a1.get('time'):
                time_a1 = transation_a1[fields_a1.get('time')]
            if fields_a1.get('source'):
                source_a1 = transation_a1[fields_a1.get('source')]

            for transation_a2 in a2.dataframe.itertuples():
                amount_a2 = transation_a2[fields_a2.get('amount')]
                date_a2 = transation_a2[fields_a2.get('date')]
                destination_a2 = transation_a2[fields_a2.get('destination')]
                if fields_a2.get('time'):
                    time_a2 = transation_a2[fields_a2.get('time')]
                if fields_a2.get('source'):
                    source_a2 = transation_a2[fields_a2.get('source')]

                for daysNumber in range(relationship[2]+1):
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

                                transactions.update({index_dict: transaction})
                                index_dict += 1

                                indexesToDrop_a1.append(transation_a1[0])
                                indexesToDrop_a2.append(transation_a2[0])
                                found = True
                                a1.dataframe.at[transation_a1[0], "Found"] = True
                                a2.dataframe.at[transation_a2[0], "Found"] = True
                                #a1.dataframe.drop(transation_a1[0], inplace=True)
                                #a2.dataframe.drop(transation_a2[0], inplace=True)
                        
                        elif (a1.account_type in [AccountType.DEBIT_CARD, AccountType.CHECKING_ACCOUNT] and a2.account_type == AccountType.PAYPAL) or (a1.account_type == AccountType.PAYPAL and a2.account_type in [AccountType.DEBIT_CARD, AccountType.CHECKING_ACCOUNT]):
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

                            if pandas.isna(source):
                                    source = "PayPal"

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

                                transactions.update({index_dict: transaction})
                                index_dict += 1

                                found = True
                                indexesToDrop_a1.append(transation_a1[0])
                                indexesToDrop_a2.append(transation_a2[0])
                                a1.dataframe.at[transation_a1[0], "Found"] = True
                                a2.dataframe.at[transation_a2[0], "Found"] = True

                                #a1.dataframe.drop(transation_a1[0], inplace=True)
                                #a2.dataframe.drop(transation_a2[0], inplace=True)
                    #if found:
                        #break
                #if found:
                    #break
        #a1.dataframe.drop(a1.dataframe.index[indexesToDrop_a1], inplace=True)
        #a2.dataframe.drop(a2.dataframe.index[indexesToDrop_a2], inplace=True)
    
    return transactions