from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from datetime import datetime
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'upload'

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        filePrefix = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        fileBank = request.files['bankFile']
        fileBankName = filePrefix+"_fileBank.csv"
        fileBank.save(os.path.join(app.config['UPLOAD_FOLDER'], fileBankName))
        fileCard = request.files['debitCardFile']
        fileCardName = filePrefix+"_fileCard.csv"
        fileCard.save(os.path.join(app.config['UPLOAD_FOLDER'], fileCardName))
        filePayPal = request.files['paypalFile']
        filePayPalName = filePrefix+"_filePayPal.csv"
        filePayPal.save(os.path.join(app.config['UPLOAD_FOLDER'], filePayPalName))
        return render_template('list_transaction.html')
    else:
        return render_template('session_manager.html')
