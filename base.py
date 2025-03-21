import csv
import re
import pandas
import compute_next_business_day
from datetime import datetime, timedelta

def getCardTransaction(csvCard, dateBank, descPartsBank):
    #fileCard.seek(0)
                        
    for lineCard in csvCard.itertuples():
        #print(lineCard)
        descPartsCard = re.split(r'\s{2,}', lineCard[4])

        datetime_card = datetime.strptime(lineCard[1], '%d/%m/%Y')

        #print("datetime_card: "+str(datetime_card))

        if dateBank == datetime_card:
            timeCard = datetime.strptime(lineCard[2], '%H:%M')
            datetime_card = datetime_card.replace(hour=timeCard.hour, minute=timeCard.minute)

            if descPartsCard[0] == descPartsBank[3]:

                #print(str(datetime_card)+" "+lineCard[3])
                print(str(datetime_card)+" "+descPartsCard[0]+" "+descPartsCard[1])
                otherAccounts.add(descPartsCard[0])


csvFileBank = pandas.read_csv('/home/michele/Downloads/Elenco_Movimenti(2).csv', decimal=',', sep=';')

csvFileCard = pandas.read_csv('/home/michele/Downloads/Elenco_Movimenti(1).csv', decimal=',', sep=';')

csvFilePayPal = pandas.read_csv('/home/michele/Downloads/L5BXD33J8AZMG-CSR-20230101000000-20250315235959-20250316052428.CSV', decimal=',')

otherAccounts = set()
for lineBank in csvFileBank.itertuples():

    datetimeBank = datetime.strptime(lineBank[2], '%d.%m.%Y')
    descPartsBank = re.split(r'\s{2,}', lineBank[3])

    print("datetime_bank: "+str(datetimeBank))

    if "MASTERCARD" in lineBank[3]:

        getCardTransaction(csvFileCard, datetimeBank, descPartsBank)
        
    elif "PayPal" in lineBank[3]:
        
        transactionFound = False
        
        for linePayPal in csvFilePayPal.itertuples():

            datetimePayPal = datetime.strptime(linePayPal[1], '%d/%m/%Y')

            #if payPalDate == datetimePayPal:
            if abs(float(lineBank[4].replace(',', '.'))) == abs(linePayPal[6]) and compute_next_business_day.next_two_business_day(datetimePayPal.strftime('%d/%m/%Y'), 'IT', '%d/%m/%Y') == datetimeBank.strftime('%d/%m/%Y'):
                print(linePayPal)
                transactionFound = True
            
        
        if not transactionFound:

            for linePayPal in csvFilePayPal.itertuples():

                
                datetimePayPal = datetime.strptime(linePayPal[1], '%d/%m/%Y')

                #if payPalDate == datetimePayPal:
                if abs(float(lineBank[4].replace(',', '.'))) == abs(linePayPal[6]) and compute_next_business_day.next_three_business_day(datetimePayPal.strftime('%d/%m/%Y'), 'IT', '%d/%m/%Y') == datetimeBank.strftime('%d/%m/%Y'):
                    print(linePayPal)
                    transactionFound = True
                

        if not transactionFound:

            rowNumberPayPal = 0
            for linePayPal in csvFilePayPal.itertuples():


                datetimePayPal = datetime.strptime(linePayPal[1], '%d/%m/%Y')

                #if payPalDate == datetimePayPal:
                if abs(float(lineBank[4].replace(',', '.'))) == abs(linePayPal[6]) and compute_next_business_day.next_business_day(datetimePayPal.strftime('%d/%m/%Y'), 'IT', '%d/%m/%Y') == datetimeBank.strftime('%d/%m/%Y'):
                    print(linePayPal)
                    transactionFound = True
            

        if not transactionFound:

            rowNumberPayPal = 0
            for linePayPal in csvFilePayPal.itertuples():

                datetimePayPal = datetime.strptime(linePayPal[1], '%d/%m/%Y')

                #if payPalDate == datetimePayPal:
                if abs(float(lineBank[4].replace(',', '.'))) == abs(linePayPal[6]) and datetimePayPal.strftime('%d/%m/%Y') == datetimeBank.strftime('%d/%m/%Y'):
                    print(linePayPal)
                    transactionFound = True
                
    #print(otherAccounts)