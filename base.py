import csv
import re
import pandas
import compute_next_business_day
from datetime import datetime, timedelta

def getCardTransaction(csvCard, dateBank, descPartsBank):
    rowNumberCard = 0
    #fileCard.seek(0)
                        
    for lineCard in csvCard:
        #print(lineCard)
        descPartsCard = re.split(r'\s{2,}', lineCard[3])

        if rowNumberCard > 0:

            datetime_card = datetime.strptime(lineCard[0], '%d/%m/%Y')

            #print("datetime_card: "+str(datetime_card))

            if dateBank == datetime_card:
                timeCard = datetime.strptime(lineCard[1], '%H:%M')
                datetime_card = datetime_card.replace(hour=timeCard.hour, minute=timeCard.minute)

                if descPartsCard[0] == descPartsBank[3]:

                    #print(str(datetime_card)+" "+lineCard[3])
                    #print(str(datetime_card)+" "+descPartsCard[0]+" "+descPartsCard[1])
                    otherAccounts.add(descPartsCard[0])

        rowNumberCard += 1


with open('/home/michele/Downloads/Elenco_Movimenti(2).csv', mode ='r') as fileBank:
    csvFileBank = csv.reader(fileBank, delimiter=';')

    with open('/home/michele/Downloads/Elenco_Movimenti(1).csv', mode ='r') as fileCard:
        csvFileCard = csv.reader(fileCard, delimiter=';')

        csvFilePayPal = pandas.read_csv('/home/michele/Downloads/L5BXD33J8AZMG-CSR-20230101000000-20250315235959-20250316052428.CSV', decimal=',')

        rowNumberBank = 0
        otherAccounts = set()
        for lineBank in csvFileBank:

            if rowNumberBank > 0:

                datetimeBank = datetime.strptime(lineBank[1], '%d.%m.%Y')
                descPartsBank = re.split(r'\s{2,}', lineBank[2])

                print("datetime_bank: "+str(datetimeBank))

                if "MASTERCARD" in lineBank[2]:
                    
                    fileCard.seek(0)

                    getCardTransaction(csvFileCard, datetimeBank, descPartsBank)
                    
                elif "PayPal" in lineBank[2]:
                    
                    rowNumberPayPal = 0
                    transactionFound = False
                    
                    for linePayPal in csvFilePayPal.itertuples():

                        datetimePayPal = datetime.strptime(linePayPal[1], '%d/%m/%Y')

                        #if payPalDate == datetimePayPal:
                        if abs(float(lineBank[3].replace(',', '.'))) == abs(linePayPal[6]) and compute_next_business_day.next_two_business_day(datetimePayPal.strftime('%d/%m/%Y'), 'IT', '%d/%m/%Y') == datetimeBank.strftime('%d/%m/%Y'):
                            print(linePayPal)
                            transactionFound = True
                        
                        rowNumberPayPal += 1
                    
                    if not transactionFound:

                        rowNumberPayPal = 0
                        for linePayPal in csvFilePayPal.itertuples():

                            
                            datetimePayPal = datetime.strptime(linePayPal[1], '%d/%m/%Y')

                            #if payPalDate == datetimePayPal:
                            if abs(float(lineBank[3].replace(',', '.'))) == abs(linePayPal[6]) and compute_next_business_day.next_three_business_day(datetimePayPal.strftime('%d/%m/%Y'), 'IT', '%d/%m/%Y') == datetimeBank.strftime('%d/%m/%Y'):
                                print(linePayPal)
                                transactionFound = True
                            
                            rowNumberPayPal += 1

                    if not transactionFound:

                        rowNumberPayPal = 0
                        for linePayPal in csvFilePayPal.itertuples():


                            datetimePayPal = datetime.strptime(linePayPal[1], '%d/%m/%Y')

                            #if payPalDate == datetimePayPal:
                            if abs(float(lineBank[3].replace(',', '.'))) == abs(linePayPal[6]) and compute_next_business_day.next_business_day(datetimePayPal.strftime('%d/%m/%Y'), 'IT', '%d/%m/%Y') == datetimeBank.strftime('%d/%m/%Y'):
                                print(linePayPal)
                                transactionFound = True
                        
                            rowNumberPayPal += 1

                    if not transactionFound:

                        rowNumberPayPal = 0
                        for linePayPal in csvFilePayPal.itertuples():


                            datetimePayPal = datetime.strptime(linePayPal[1], '%d/%m/%Y')

                            #if payPalDate == datetimePayPal:
                            if abs(float(lineBank[3].replace(',', '.'))) == abs(linePayPal[6]) and datetimePayPal.strftime('%d/%m/%Y') == datetimeBank.strftime('%d/%m/%Y'):
                                print(linePayPal)
                                transactionFound = True
                            
                            rowNumberPayPal += 1

            rowNumberBank += 1
            #print(otherAccounts)