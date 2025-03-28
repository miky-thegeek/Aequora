from flask import Flask, render_template, request, redirect
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from base import unicreditMain
from firefly_iii import FireflyIII
from collections import defaultdict
import csv

import pandas
from transaction import FinancialTransaction, TransactionType
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'upload'

fireflyIII = FireflyIII("http://192.168.1.30:8081/", os.environ["fireflyIII_id"], os.environ["fireflyIII_secret"])

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':

        if not fireflyIII.checkAccessToken():
            return redirect(fireflyIII.startAuth())

        filePrefix = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

        if "previousSessionFile" in request.files:
            previousSessionFile = request.files['previousSessionFile']
            previousSessionFilePath = os.path.join(app.config['UPLOAD_FOLDER'], filePrefix+"_fileSession.csv")
            previousSessionFile.save(previousSessionFilePath)

            transactionsNotExistend = {}
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

                transactionsNotExistend.update({i: financialTransaction})
                i += 1
            return render_template('list_transaction.html', transactions=transactionsNotExistend)
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

            transactionsSorted = sorted(transactions, key=lambda x: (x.date, x.amount))

            transactionsNotExistend = {}
            i = 0
            j = 0
            #for j in range(len(transactionsSorted)):
            while j < len(transactionsSorted):
                query = "amount:"+('{:.2f}'.format(transactionsSorted[j].amount))+" date_on:"+transactionsSorted[j].date.strftime('%Y-%m-%d')
                
                goNext = True
                k = j + 1
                n = 1
                
                if (k != len(transactionsSorted)):
                    while(goNext):
                        #print('j: '+str(j)+' k: '+str(k)+" len transactionsSorted"+str(len(transactionsSorted)))
                        if (transactionsSorted[j].amount == transactionsSorted[k].amount) and (transactionsSorted[j].date.strftime('%Y-%m-%d') == transactionsSorted[k].date.strftime('%Y-%m-%d')):
                            n += 1
                            goNext = True
                        else:
                            goNext = False
                        if (k != len(transactionsSorted) - 1):
                            k += 1
                
                
                result = fireflyIII.searchTransations(query)

                if len(result["data"]) != n:
                    #print("IF n: "+str(n)+"len result: "+str(len(result["data"])) )
                    print("IF query: "+query+" n: "+str(n)+" j: "+str(j)+" k: "+str(k))
                    query = "amount:"+('{:.2f}'.format(transactionsSorted[j].amount * n))+" date_on:"+transactionsSorted[j].date.strftime('%Y-%m-%d')

                    result = fireflyIII.searchTransations(query)

                    if len(result["data"]) != 1:
                        #print("IF IF n: "+str(n)+"len result: "+str(len(result["data"])) )
                        print("IF IF query: "+query+" n: "+str(n)+" j: "+str(j)+" k: "+str(k))
                        #print(transaction)
                        transactionsNotExistend.update({i: transactionsSorted[j]})
                        i += 1
                j += n
                print("j: "+str(j))

            return render_template('list_transaction.html', transactions=transactionsNotExistend)
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
        fieldnames = ['date', 'transactionType', 'sourceAccount', 'destinationAccount', 'description', 'amount']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    return str(grouped_data)

if __name__ == "__main__":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    context = ('certs/server.crt', 'certs/server.key')
    app.run(host='0.0.0.0', port=8443, debug=True, ssl_context=context)