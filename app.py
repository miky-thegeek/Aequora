from flask import Flask, render_template, request, redirect, send_file
from datetime import datetime
import os
from base import unicreditMain
from firefly_iii import FireflyIII
from collections import defaultdict
import csv
import json

import pandas
from transaction import FinancialTransaction, TransactionType
from account import Account, AccountType
from datetime import datetime
import normalization
import base_v2

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'upload'

fireflyIII = FireflyIII("http://192.168.1.30:8081/", os.environ["fireflyIII_id"], os.environ["fireflyIII_secret"])


def generate_dynamic_relationship(accounts):
    relazioni = []

    for a1 in accounts:
        for a2 in accounts:
            if a1.id == a2.id:
                continue

            t1 = a1.account_type
            t2 = a2.account_type

            # Regola 1: debito → solo con conto associato
            if t1 == AccountType.DEBIT_CARD and t2 == AccountType.CHECKING_ACCOUNT and a1.id_associated_account == a2.id:
                relazioni.append((a1.id, a2.id, [0]))

            # Regola 2: paypal → conto
            elif t1 == AccountType.PAYPAL and t2 == AccountType.CHECKING_ACCOUNT:
                relazioni.append((a1.id, a2.id, [0, 1, 2, 3]))

            # Regola 2: paypal → prepagata
            elif t1 == AccountType.PAYPAL and t2 == AccountType.PREPAID_CARD:
                relazioni.append((a1.id, a2.id, [-1, 0, 1]))

            # Regola 3: prepagata → conto
            elif t1 == AccountType.PREPAID_CARD and t2 == AccountType.CHECKING_ACCOUNT:
                relazioni.append((a1.id, a2.id, [1]))

            # Altri casi personalizzabili qui...
    
    return relazioni

def listToDict(transactions_list):
    i = 0
    transactions_dict = {}
    for transaction in transactions_list:
        transactions_dict[i] = transaction
        i += 1
    return transactions_dict

@app.route('/', methods=['GET'])
def index():
	if not fireflyIII.checkAccessToken():
		return redirect(fireflyIII.startAuth())
	return render_template('session_manager.html')

@app.route('/new_session', methods=['POST'])
def new_session():

    if not fireflyIII.checkAccessToken():
        return redirect(fireflyIII.startAuth())
    
    categories = fireflyIII.getCategories()
    accounts = {}
    config = {}
    with open('config.json', 'r') as file:
        config = json.load(file)

    filePrefix = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    for key, value in request.files.items():
        fileAccount = request.files[key]
        fileAccountPath = os.path.join(app.config['UPLOAD_FOLDER'], filePrefix+"_"+key+".csv")
        fileAccount.save(fileAccountPath)

        account = base_v2.get_account_from_key(key, request)

        if account.account_type == AccountType.DEBIT_CARD:
            associated_bank = accounts[account.id_associated_account].bank
        else:
            associated_bank = None

        df = base_v2.get_dataset(account, fileAccountPath, config, associated_bank)
        normalization_fn = base_v2.get_normalization_function(account, config, normalization, associated_bank)
        df = base_v2.process_dataframe(df, normalization_fn)
        
        account.setDataframe(df)
        os.remove(fileAccountPath)
        
        accounts.update({key: account})

    relations = generate_dynamic_relationship(list(accounts.values()))

    print(relations)

    transactions = base_v2.compare_accounts(accounts, relations, config)

    for account in accounts.values():
        if account.account_type in [AccountType.CHECKING_ACCOUNT, AccountType.PREPAID_CARD]:
            elaborate_single_account = getattr(base_v2, "elaborate_"+account.account_type.value+"_"+account.bank.lower())

            list_transactions = elaborate_single_account(account, config)
            transactions.extend(list_transactions)
            
        elif account.account_type ==  AccountType.PAYPAL:
            elaborate_single_account = getattr(base_v2, "elaborate_"+AccountType.PAYPAL.value)

            list_transactions = elaborate_single_account(account, config)
            transactions.extend(list_transactions)
            

    transactions = base_v2.findSourceDestinationCategoryID(transactions, fireflyIII)
    transactionsNotExistend = base_v2.checkExistingTransations(transactions, fireflyIII)
    transactions_dict = listToDict(transactionsNotExistend)

    for account in accounts.values():
        account.dataframe.to_csv(os.path.join(app.config['UPLOAD_FOLDER'], account.id+".csv"), sep=',', encoding='utf-8', index=False, header=True)

    return render_template('list_transaction.html', transactions=transactions_dict, categories=categories)

@app.route('/continue_session', methods=['POST'])
def continue_session():
    if not fireflyIII.checkAccessToken():
        return redirect(fireflyIII.startAuth())
    
    categories = fireflyIII.getCategories()

    filePrefix = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    previousSessionFile = request.files['previousSessionFile']
    previousSessionFilePath = os.path.join(app.config['UPLOAD_FOLDER'], filePrefix+"_fileSession.csv")
    previousSessionFile.save(previousSessionFilePath)

    csvFileSession = pandas.read_csv(previousSessionFilePath)
    os.remove(previousSessionFilePath)

    transactions = base_v2.read_previous_transactions(csvFileSession)

    transactions = base_v2.findSourceDestinationCategoryID(transactions, fireflyIII)

    transactionsNotExistend = base_v2.checkExistingTransations(transactions, fireflyIII)

    transactions_dict = listToDict(transactionsNotExistend)

    return render_template('list_transaction.html', transactions=transactions_dict, categories=categories)
    

@app.route('/oauth2_callback', methods=['GET'])
def oauth2_callback():

    result = fireflyIII.continueAuth(request.args.get('code'))

    print("oauth2_callback: "+str(result))

    return redirect('/')

@app.route('/save', methods=['POST'])
def save():
    # Dizionario per raggruppare i dati
    grouped_data = defaultdict(dict)

    # Raggruppamento dei dati
    for key, value in request.form.items():
        prefix, suffix = key.rsplit('_', 1)
        grouped_data[suffix][prefix] = value

    csv_rows = []
    for key, value in grouped_data.items():
        csv_rows.append(value)

    filePrefix = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    fileOutputPath = os.path.join(app.config['UPLOAD_FOLDER'], filePrefix+"_fileTransactions.csv")
    
    with open(fileOutputPath, 'w', newline='') as csvfile:
        fieldnames = ['date', 'transactionType', 'sourceAccount', 'destinationAccount', 'description', 'amount', 'category', 'sourceAccountId', 'destinationAccountId']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    #return str(grouped_data)
    return send_file(fileOutputPath, as_attachment=True)

@app.route('/insert', methods=['POST'])
def insert():

    # Dizionario per raggruppare i dati
    grouped_data = defaultdict(dict)

    # Raggruppamento dei dati
    for key, value in request.form.items():
        prefix, suffix = key.rsplit('_', 1)
        grouped_data[suffix][prefix] = value

    csv_rows = []
    results = []
    for key, value in grouped_data.items():
        csv_rows.append(value)

        fireflyTransaction = {"type": value.get('transactionType'), 'date': value.get('date'), 
                              "amount": value.get('amount'), "description": value.get('description'), 
                              "currency_code": "EUR", "category_id": value.get('category')}


        sourceAccountId = value.get('sourceAccountId')
        if sourceAccountId == "None":
            sourceAccountsFirefly = fireflyIII.autocompleteAccounts(value.get('sourceAccount'), "Revenue account")
            if len(sourceAccountsFirefly) > 0:
                fireflyTransaction['source_id'] = sourceAccountsFirefly[0].get('id')
            else:
                fireflyTransaction['source_name'] = value.get('sourceAccount')
        else:
            fireflyTransaction['source_id'] = sourceAccountId
        
        
        if value.get('destinationAccountId') == "None":
            destinationAccountsFirefly = fireflyIII.autocompleteAccounts(value.get('destinationAccount'), "Expense account")
            if len(destinationAccountsFirefly) > 0:
                fireflyTransaction['destination_id'] = destinationAccountsFirefly[0].get('id')
            else:
                fireflyTransaction['destination_name'] = value.get('destinationAccount')
        else:
            fireflyTransaction['destination_id'] = value.get('destinationAccountId')
        #print(value)

        data = {"error_if_duplicate_hash": False, "apply_rules": True, "fire_webhooks": True, "transactions": [fireflyTransaction]}

        result = fireflyIII.insertTransactions(data)
        print(result)
        results.append(result)
        #dataJSON = json.dumps(data)

    return json.dumps(results)

if __name__ == "__main__":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    context = ('certs/server.crt', 'certs/server.key')
    app.run(host='0.0.0.0', port=8443, debug=True, ssl_context=context)
