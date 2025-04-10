from flask import Flask, render_template, request, redirect, send_file
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from base import unicreditMain
from firefly_iii import FireflyIII
from collections import defaultdict
import csv
import json

import pandas
from transaction import FinancialTransaction, TransactionType
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'upload'

fireflyIII = FireflyIII("http://192.168.1.30:8081/", os.environ["fireflyIII_id"], os.environ["fireflyIII_secret"])

def checkExistingTransations(sourceTransations, fireflyAssetId):
    transactionsSorted = sorted(sourceTransations, key=lambda x: (x.date, x.amount))

    transactionsNotExistend = {}
    i = 0
    j = 0

    while j < len(transactionsSorted):
        query = "account_id:"+fireflyAssetId+" amount:"+('{:.2f}'.format(transactionsSorted[j].amount))+" date_on:"+transactionsSorted[j].date.strftime('%Y-%m-%d')
        
        goNext = True
        k = j + 1
        n = 1
        
        if (k != len(transactionsSorted)):
            while(goNext):
                if (transactionsSorted[j].amount == transactionsSorted[k].amount) and (transactionsSorted[j].date.strftime('%Y-%m-%d') == transactionsSorted[k].date.strftime('%Y-%m-%d')):
                    n += 1
                    goNext = True
                else:
                    goNext = False
                if (k != len(transactionsSorted) - 1):
                    k += 1
        
        
        result = fireflyIII.searchTransations(query)

        if len(result["data"]) != n:
            query = "account_id:"+fireflyAssetId+" amount:"+('{:.2f}'.format(transactionsSorted[j].amount * n))+" date_on:"+transactionsSorted[j].date.strftime('%Y-%m-%d')

            result = fireflyIII.searchTransations(query)

            if len(result["data"]) != 1:
                for z in range(j, j+n):
                    transactionsNotExistend.update({i: transactionsSorted[z]})
                    i += 1
        j += n
    return transactionsNotExistend

def getMostUsedCategoryID(accountTransaction):

    categories = {}
    if "data" in accountTransaction:
        for singleData in accountTransaction.get('data'):
            for transaction in singleData.get('attributes').get('transactions'):
                category_id = transaction.get('category_id')
                if category_id in categories:
                    categories.update({category_id: categories[category_id]+1})
                else:
                    categories.update({category_id: 1})
    if len(categories) > 0:
        return max(categories, key=categories.get)
    else:
        return -1

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':

        if not fireflyIII.checkAccessToken():
            return redirect(fireflyIII.startAuth())
        
        categories = fireflyIII.getCategories()

        filePrefix = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

        if "previousSessionFile" in request.files:
            previousSessionFile = request.files['previousSessionFile']
            previousSessionFilePath = os.path.join(app.config['UPLOAD_FOLDER'], filePrefix+"_fileSession.csv")
            previousSessionFile.save(previousSessionFilePath)

            transactions = []
            i = 0
            csvFileSession = pandas.read_csv(previousSessionFilePath)
            os.remove(previousSessionFilePath)

            for lineSession in csvFileSession.itertuples():

                if lineSession[2] == "withdrawal":
                    transactionType = TransactionType.WITHDRAWAL
                elif lineSession[2] == "deposit":
                    transactionType = TransactionType.DEPOSIT
                else:
                    transactionType = TransactionType.TRANSFER

                date = datetime.strptime(lineSession[1], '%Y-%m-%dT%H:%M')

                financialTransaction = FinancialTransaction(transactionType, date, "EUR", lineSession[6], lineSession[3], lineSession[4])

                if not pandas.isna(lineSession[5]):
                    financialTransaction.setDescription(lineSession[5])

                sourceAccount = lineSession[3]
                if pandas.isna(sourceAccount):
                    sourceAccount = ""
                sourceAccountsFirefly = fireflyIII.autocompleteAccounts(sourceAccount, "Revenue account")
                if len(sourceAccountsFirefly) > 0:
                    financialTransaction.setSourceAccountID(sourceAccountsFirefly[0].get('id'))
                
                destinationAccount = lineSession[4]
                if pandas.isna(destinationAccount):
                    destinationAccount = ""
                destinationAccountsFirefly = fireflyIII.autocompleteAccounts(destinationAccount, "Expense account")
                if len(destinationAccountsFirefly) > 0:
                    financialTransaction.setDestinationAccountID(destinationAccountsFirefly[0].get('id'))

                if pandas.isna(lineSession[7]):
                    print("isna")
                    accountCounterpartyID = financialTransaction.getAccountCounterparty("Unicredit").get('id')
                    if accountCounterpartyID is not None:
                        accountTransactions = fireflyIII.getTransactionsOfAccount(accountCounterpartyID)
                        financialTransaction.setCategoryID(getMostUsedCategoryID(accountTransactions))
                else:
                    financialTransaction.setCategoryID(lineSession[7])



                transactions.append(financialTransaction)
                i += 1
            
            transactionsNotExistend = checkExistingTransations(transactions, "1")

            return render_template('list_transaction.html', transactions=transactionsNotExistend, categories=categories)
        else:
            
            fileBank = request.files['bankFile']
            fileBankPath = os.path.join(app.config['UPLOAD_FOLDER'], filePrefix+"_fileBank.csv")
            fileBank.save(fileBankPath)

            fileCard = request.files['debitCardFile']
            fileCardPath = os.path.join(app.config['UPLOAD_FOLDER'], filePrefix+"_fileCard.csv")
            fileCard.save(fileCardPath)

            filePayPal = request.files['paypalFile']
            filePayPalPath = os.path.join(app.config['UPLOAD_FOLDER'], filePrefix+"_filePayPal.csv")
            filePayPal.save(filePayPalPath)

            transactions = unicreditMain(fileBankPath, fileCardPath, filePayPalPath)

            os.remove(fileBankPath)
            os.remove(fileCardPath)
            os.remove(filePayPalPath)

            transactionsNotExistend = checkExistingTransations(transactions, "1")

            return render_template('list_transaction.html', transactions=transactionsNotExistend, categories=categories)
    else:
        if not fireflyIII.checkAccessToken():
            return redirect(fireflyIII.startAuth())
        return render_template('session_manager.html')
    
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