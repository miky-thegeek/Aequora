from datetime import timedelta
import pandas
def normalizeBank(csvBank):
    for lineBank in csvBank.itertuples():
        csvBank.at[lineBank[0], 'Importo (EUR)'] = float(lineBank[4].replace('.', '').replace(',', '.'))

def normalizePayPal(csvPayPal):
    #pagamenti = csvPayPal[csvPayPal['Descrizione'].str.contains('Pagamento|Rimborso')]
    pagamenti = csvPayPal.copy()
    addebiti = csvPayPal[csvPayPal['Descrizione'].str.contains('Bonifico|Versamento generico con carta|Pagamento con credito acquirenti PayPal|Trasferimento avviato dall\'utente|Prelievo')]
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
