from datetime import timedelta, datetime
from dateutil import parser
import pandas
import re

def normalizeBank(csvBank):
    """Normalize bank CSV data by converting amount format.
    
    Converts amount values from European format (e.g., "1.234,56") to
    float format by removing thousand separators and converting comma
    to decimal point.
    
    Args:
        csvBank (pandas.DataFrame): DataFrame containing bank transaction data
                                  with 'Importo (EUR)' column in European format.
    """
    for lineBank in csvBank.itertuples():
        csvBank.at[lineBank[0], 'Importo (EUR)'] = float(lineBank[4].replace('.', '').replace(',', '.'))

def normalizePayPal(csvPayPal):
    """Normalize PayPal CSV data by removing duplicate transactions.
    
    Processes PayPal transactions by identifying and removing duplicate
    entries (addebiti) that correspond to payments (pagamenti), and
    updates bank information in the DataFrame.
    
    Args:
        csvPayPal (pandas.DataFrame): DataFrame containing PayPal transaction
                                    data with columns for description, amount,
                                    currency, date, and bank information.
    """
    pagamenti = csvPayPal.copy()
    addebiti = csvPayPal[csvPayPal['Descrizione'].str.contains('Bonifico|Versamento generico con carta|Pagamento con credito acquirenti PayPal|Trasferimento avviato dall\'utente|Prelievo|Blocco conto per autorizzazione aperta|Storno di blocco conto generico')]
    for index, pagamento in addebiti.iterrows():
        pagamenti.drop(index, inplace=True)

    indexes_to_drop = []
    # Rimuovere gli addebiti corrispondenti ai pagamenti
    for index, pagamento in pagamenti.iterrows():
        importo = pagamento.iloc[5]
        valuta = pagamento.iloc[4]
        data = pagamento.iloc[0]

        # Trova una riga 'Addebito' con la stessa valuta e importo negativo corrispondente
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

        # Se esiste una corrispondenza, rimuoverla
    if len(indexes_to_drop) > 0:
        csvPayPal.drop(csvPayPal.index[indexes_to_drop], inplace=True)

def normalizePostePay(csvPostePay):
    """Normalize PostePay CSV data by extracting and parsing time information.
    
    Extracts time information from transaction descriptions using regex
    pattern matching and adds a 'Time' column to the DataFrame. If no
    time is found, sets time to midnight.
    
    Args:
        csvPostePay (pandas.DataFrame): DataFrame containing PostePay transaction
                                      data with description column containing
                                      date/time information.
    """
    regex = r"[0-9]{2}\/[0-9]{2}\/[0-9]{4}\s+[0-9]{2}[\.\:][0-9]{2}"

    for row in csvPostePay.itertuples():
        desc = row[4]

        finds = re.findall(regex, desc)

        if len(finds) > 0:
            date_object = parser.parse(finds[0].replace('.', ':'))

            csvPostePay.at[row[0], "Time"] = date_object

        else:
            csvPostePay.at[row[0], "Time"] = datetime.now().replace(hour=0, minute=0)

