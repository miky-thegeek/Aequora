def normalizeBank(csvBank):
    for lineBank in csvBank.itertuples():
        csvBank.at[lineBank[0], 'Importo (EUR)'] = float(lineBank[4].replace('.', '').replace(',', '.'))

def normalizePayPal(csvPayPal):
    pagamenti = csvPayPal[csvPayPal['Descrizione'].str.contains('Pagamento')]
    addebiti = csvPayPal[csvPayPal['Descrizione'].str.contains('Bonifico|Versamento generico con carta|Pagamento con credito acquirenti PayPal')]

    indexes_to_drop = []
    # Rimuovere gli addebiti corrispondenti ai pagamenti
    for index, pagamento in pagamenti.iterrows():
        importo = pagamento.iloc[5]
        valuta = pagamento.iloc[4]

        # Trova una riga 'Addebito' con la stessa valuta e importo negativo corrispondente
        addebito_match = addebiti[
            (addebiti['Valuta'] == valuta) &
            (-addebiti['Lordo '] == importo)
        ].index
        indexes_to_drop.extend(addebito_match.to_list())

        # Se esiste una corrispondenza, rimuoverla
    if len(indexes_to_drop) > 0:
        csvPayPal.drop(csvPayPal.index[indexes_to_drop], inplace=True)
