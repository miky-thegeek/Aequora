from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from base import unicreditMain

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'upload'

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

        return render_template('list_transaction.html', transactions=transactions)
    else:
        return render_template('session_manager.html')
