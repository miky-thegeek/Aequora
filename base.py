import re
import pandas
import compute_next_business_day
import normalization
from transaction import FinancialTransaction, TransactionType
from datetime import datetime

def getCardTransaction(csvCard, dateBank, descPartsBank):
                        
    for lineCard in csvCard.itertuples():
        #print(lineCard)
        descPartsCard = re.split(r'\s{2,}', lineCard[4])

        if dateBank == lineCard[1]:
            datetime_card = lineCard[1].to_pydatetime()
            datetime_card = datetime_card.replace(hour=lineCard[2].hour, minute=lineCard[2].minute)

            if descPartsCard[0] == descPartsBank[3]:

                #print(str(datetime_card)+" "+descPartsCard[0]+" "+descPartsCard[1])
                #otherAccounts.add(descPartsCard[0])

                transaction = FinancialTransaction(
                    transaction_type=TransactionType.WITHDRAWAL,
                    date=datetime_card,
                    currency_code="EUR",
                    amount=abs(lineCard[5]),
                    source_account="Unicredit",
                    destination_account=descPartsCard[0]
                )

                return transaction
            elif descPartsCard[0] == descPartsBank[4]:

                #print(str(datetime_card)+" "+descPartsCard[0]+" "+descPartsCard[1])
                #otherAccounts.add(descPartsCard[0])

                transaction = FinancialTransaction(
                    transaction_type=TransactionType.WITHDRAWAL,
                    date=datetime_card,
                    currency_code="EUR",
                    amount=abs(lineCard[5]),
                    source_account="Unicredit",
                    destination_account=descPartsCard[0]
                )

                return transaction

def getPayPalTransaction(csvPayPal, ammount_bank, date_bank):
    #idDataset = -1

    for linePayPal in csvPayPal.itertuples():
        datetimePayPal = linePayPal[1].to_pydatetime()

        for daysNumber in [2, 3, 1, 0]:
            if abs(ammount_bank) == abs(linePayPal[6]) and compute_next_business_day.next_number_business_day(datetimePayPal, 'IT', daysNumber) == date_bank:
                datetimePayPal.replace(hour=linePayPal[2].hour, minute=linePayPal[2].minute)
                #print(linePayPal)
                #idDataset = linePayPal[0]

                if ammount_bank > 0:
                    transactionType = TransactionType.DEPOSIT
                    sourceAccount = linePayPal[12]
                    destinationAccount = "Unicredit"
                else:
                    transactionType = TransactionType.WITHDRAWAL
                    sourceAccount = "Unicredit"
                    destinationAccount = linePayPal[12]

                transaction = FinancialTransaction(
                    transaction_type=transactionType,
                    date=datetimePayPal,
                    currency_code="EUR",
                    amount=abs(linePayPal[6]),
                    source_account=sourceAccount,
                    destination_account=destinationAccount
                )

                return transaction
            
            #if idDataset != -1:
                #break
        #if idDataset != -1:
                #break


csvFileBank = pandas.read_csv('/home/michele/Downloads/Elenco_Movimenti(2).csv', decimal=",", sep=';', parse_dates=[0, 1], dayfirst=True)

csvFileCard = pandas.read_csv('/home/michele/Downloads/Elenco_Movimenti(1).csv', decimal=',', sep=';', parse_dates=[0, 1, 2], dayfirst=True, date_format={'Data Registrazione': '%d/%m/%Y', 'Ora operazione': '%H:%M', 'Data valuta': '%d/%m/%Y'})

csvFilePayPal = pandas.read_csv('/home/michele/Downloads/L5BXD33J8AZMG-CSR-20230101000000-20250315235959-20250316052428.CSV', decimal=',', low_memory=False, parse_dates=[0, 1], dayfirst=True, date_format={'Data': '%d/%m/%Y', 'Ora': '%H:%M:%S'})

normalization.normalizeBank(csvFileBank)

normalization.normalizePayPal(csvFilePayPal)
#print(csvFilePayPal)

transactions = []
otherAccounts = set()
for lineBank in csvFileBank.itertuples():

    descPartsBank = re.split(r'\s{2,}', lineBank[3])

    #print("datetime_bank: "+str(lineBank[2].to_pydatetime()))

    if "MASTERCARD" in lineBank[3]:

        transaction = getCardTransaction(csvFileCard, lineBank[2], descPartsBank)
        if transaction == None:
            print("NULL MASTERCARD")
        transactions.append(transaction)
        
    elif "PayPal" in lineBank[3]:

        transaction = getPayPalTransaction(csvFilePayPal, lineBank[4], lineBank[2].to_pydatetime())
        if transaction == None:
            print("NULL PayPal")
        else:
            transactions.append(transaction)

    elif "VOSTRI EMOLUMENTI" in lineBank[3]:
        transaction = FinancialTransaction(
            transaction_type=TransactionType.DEPOSIT,
            date=lineBank[2].to_pydatetime(),
            currency_code="EUR",
            amount=lineBank[4],
            source_account=descPartsBank[2],
            destination_account="Unicredit"
        )
        transaction.setDescription(descPartsBank[3]+descPartsBank[4])
        transactions.append(transaction)
    
    elif "FINDOMESTIC" in lineBank[3].upper():
        transaction = FinancialTransaction(
            transaction_type=TransactionType.TRANSFER,
            date=lineBank[2].to_pydatetime(),
            currency_code="EUR",
            amount=abs(lineBank[4]),
            source_account="Unicredit",
            destination_account="Findomestic"
        )
        transactions.append(transaction)
    
    elif "ADDEBITO SEPA DD" in lineBank[3].upper():
        transaction = FinancialTransaction(
            transaction_type=TransactionType.WITHDRAWAL,
            date=lineBank[2].to_pydatetime(),
            currency_code="EUR",
            amount=abs(lineBank[4]),
            source_account="Unicredit",
            destination_account=descPartsBank[3]
        )
        transactions.append(transaction)
    
    elif "PRELIEVO" in lineBank[3].upper():
        transaction = FinancialTransaction(
            transaction_type=TransactionType.TRANSFER,
            date=lineBank[2].to_pydatetime(),
            currency_code="EUR",
            amount=abs(lineBank[4]),
            source_account="Unicredit",
            destination_account="Contanti"
        )
        transactions.append(transaction)

    elif "BONIFICO A VOSTRO FAVORE" in lineBank[3].upper():

        if "BONIFICO SEPA" in descPartsBank[1]:
            description = descPartsBank[3]+descPartsBank[4]
        else:
            description = descPartsBank[1]

        transaction = FinancialTransaction(
            transaction_type=TransactionType.DEPOSIT,
            date=lineBank[2].to_pydatetime(),
            currency_code="EUR",
            amount=abs(lineBank[4]),
            source_account=descPartsBank[2],
            destination_account="Unicredit"
        )
        transaction.setDescription(description)
        transactions.append(transaction)

    elif "DISPOSIZIONE DI BONIFICO" in lineBank[3].upper():
        transaction = FinancialTransaction(
            transaction_type=TransactionType.WITHDRAWAL,
            date=lineBank[2].to_pydatetime(),
            currency_code="EUR",
            amount=abs(lineBank[4]),
            source_account="Unicredit",
            destination_account=descPartsBank[2]
        )
        transaction.setDescription(descPartsBank[1])
        transactions.append(transaction)

    elif "DISPOSIZIONE DI ADDEBITO" in lineBank[3].upper():
        transaction = FinancialTransaction(
            transaction_type=TransactionType.WITHDRAWAL,
            date=lineBank[2].to_pydatetime(),
            currency_code="EUR",
            amount=abs(lineBank[4]),
            source_account="Unicredit",
            destination_account=descPartsBank[1]
        )
        transactions.append(transaction)
    
    elif "COMMISSIONI - PROVVIGIONI - SPESE" in lineBank[3].upper():
        transaction = FinancialTransaction(
            transaction_type=TransactionType.WITHDRAWAL,
            date=lineBank[2].to_pydatetime(),
            currency_code="EUR",
            amount=abs(lineBank[4]),
            source_account="Unicredit",
            destination_account="Banca Unicredit"
        )
        transaction.setDescription(descPartsBank[1])
        transactions.append(transaction)

    elif "IMPOSTA BOLLO" in lineBank[3].upper():
        transaction = FinancialTransaction(
            transaction_type=TransactionType.WITHDRAWAL,
            date=lineBank[2].to_pydatetime(),
            currency_code="EUR",
            amount=abs(lineBank[4]),
            source_account="Unicredit",
            destination_account="Banca Unicredit"
        )
        transaction.setDescription(descPartsBank[0])
        transactions.append(transaction)
    
    elif "CARTA *3455" in lineBank[3].upper():
        transaction = FinancialTransaction(
            transaction_type=TransactionType.WITHDRAWAL,
            date=lineBank[2].to_pydatetime(),
            currency_code="EUR",
            amount=abs(lineBank[4]),
            source_account="Unicredit",
            destination_account=descPartsBank[4]
        )
        transactions.append(transaction)

    elif "VERSAMENTO" in lineBank[3].upper():
        transaction = FinancialTransaction(
            transaction_type=TransactionType.DEPOSIT,
            date=lineBank[2].to_pydatetime(),
            currency_code="EUR",
            amount=abs(lineBank[4]),
            source_account="Risparmi",
            destination_account="Unicredit"
        )
        transactions.append(transaction)
    
    elif "ACCREDITI VARI" in lineBank[3].upper():
        transaction = FinancialTransaction(
            transaction_type=TransactionType.DEPOSIT,
            date=lineBank[2].to_pydatetime(),
            currency_code="EUR",
            amount=abs(lineBank[4]),
            source_account="Banca Unicredit",
            destination_account="Unicredit"
        )
        transaction.setDescription(descPartsBank[1])
        transactions.append(transaction)

    else:
        print(lineBank)

    #print(otherAccounts)
#print(transactions)