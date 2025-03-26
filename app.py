from flask import Flask, render_template, request, redirect
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from base import unicreditMain
from firefly_iii import FireflyIII

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'upload'

fireflyIII = FireflyIII(os.environ["fireflyIII_id"], os.environ["fireflyIII_secret"])

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        filePrefix = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        
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

        #transactionsSorted = sorted(transactions, key=lambda x: (x.date, x.amount))

        transactionsNotExistend = []
        for transaction in transactions:
            query = "amount:"+('{:.2f}'.format(transaction.amount))+" date_on:"+transaction.date.strftime('%Y-%m-%d')

            result = fireflyIII.searchTransations(query)

            if len(result["data"]) == 0:
                transactionsNotExistend.append(transaction)

        return render_template('list_transaction.html', transactions=transactionsNotExistend)
    else:
        if not fireflyIII.checkAccessToken():
            return redirect(fireflyIII.startAuth())
        return render_template('session_manager.html')
    
@app.route('/oauth2_callback', methods=['POST', 'GET'])
def oauth2_callback():

    result = fireflyIII.continueAuth(request.args.get('code'))

    print("oauth2_callback: "+str(result))

    return redirect('/')

if __name__ == "__main__":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    context = ('certs/server.crt', 'certs/server.key')
    app.run(host='0.0.0.0', port=8443, debug=True, ssl_context=context)