from datetime import timedelta
def normalizeBank(csvBank):
    for lineBank in csvBank.itertuples():
        csvBank.at[lineBank[0], 'Importo (EUR)'] = float(lineBank[4].replace('.', '').replace(',', '.'))

def normalizePayPal(csvPayPal):
    pagamenti = csvPayPal[csvPayPal['Descrizione'].str.contains('Pagamento|Rimborso')]
    addebiti = csvPayPal[csvPayPal['Descrizione'].str.contains('Bonifico|Versamento generico con carta|Pagamento con credito acquirenti PayPal|Trasferimento avviato dall\'utente|Prelievo')]

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
                csvPayPal.iat[index, 12] = bank
        indexes_to_drop.extend(addebito_match.to_list())

        # Se esiste una corrispondenza, rimuoverla
    if len(indexes_to_drop) > 0:
        csvPayPal.drop(csvPayPal.index[indexes_to_drop], inplace=True)
