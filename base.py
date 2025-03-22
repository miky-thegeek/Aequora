import re
import pandas
import compute_next_business_day
import decimal
from datetime import datetime

def getCardTransaction(csvCard, dateBank, descPartsBank):
                        
    for lineCard in csvCard.itertuples():
        #print(lineCard)
        descPartsCard = re.split(r'\s{2,}', lineCard[4])

        if dateBank == lineCard[1]:
            datetime_card = lineCard[1].to_pydatetime()
            datetime_card = datetime_card.replace(hour=lineCard[2].hour, minute=lineCard[2].minute)

            if descPartsCard[0] == descPartsBank[3]:

                #print(str(datetime_card)+" "+lineCard[3])
                print(str(datetime_card)+" "+descPartsCard[0]+" "+descPartsCard[1])
                #otherAccounts.add(descPartsCard[0])

def getPayPalTransaction(csvPayPal, ammount_bank, date_bank):
    idDataset = -1

    for linePayPal in csvPayPal.itertuples():

        for daysNumber in [2, 3, 1, 0]:
            if abs(ammount_bank) == abs(linePayPal[6]) and compute_next_business_day.next_number_business_day(linePayPal[1].to_pydatetime(), 'IT', daysNumber) == date_bank:
                print(linePayPal)
                idDataset = linePayPal[0]
            
            if idDataset != -1:
                break
        if idDataset != -1:
                break

csvFileBank = pandas.read_csv('/home/michele/Downloads/Elenco_Movimenti(2).csv', decimal=",", sep=';', parse_dates=[0, 1], dayfirst=True)

csvFileCard = pandas.read_csv('/home/michele/Downloads/Elenco_Movimenti(1).csv', decimal=',', sep=';', parse_dates=[0, 1, 2], dayfirst=True)

csvFilePayPal = pandas.read_csv('/home/michele/Downloads/L5BXD33J8AZMG-CSR-20230101000000-20250315235959-20250316052428.CSV', decimal=',', parse_dates=[0, 1], dayfirst=True)

otherAccounts = set()
for lineBank in csvFileBank.itertuples():

    descPartsBank = re.split(r'\s{2,}', lineBank[3])

    #csvFileBank.at[lineBank[0], 'Importo (EUR)'] = float(lineBank[4].replace(',', '.'))

    print("datetime_bank: "+str(lineBank[2].to_pydatetime()))

    if "MASTERCARD" in lineBank[3]:

        getCardTransaction(csvFileCard, lineBank[2], descPartsBank)
        
    elif "PayPal" in lineBank[3]:

        getPayPalTransaction(csvFilePayPal, float(lineBank[4].replace(',', '.')), lineBank[2].to_pydatetime())

    #print(otherAccounts)