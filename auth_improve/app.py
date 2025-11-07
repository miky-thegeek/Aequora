from flask import Flask, render_template, request, redirect, send_file
from datetime import datetime
import os
from firefly_iii import FireflyIII
from collections import defaultdict
import csv
import json
import logging

import pandas
from entities.transaction import FinancialTransaction, TransactionType
from entities.account import Account, AccountType
from datetime import datetime
import normalization
import base_v2

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'upload'

# Validate environment variables
fireflyIII_id = os.environ.get("fireflyIII_id")
fireflyIII_secret = os.environ.get("fireflyIII_secret")

if not fireflyIII_id or not fireflyIII_secret:
    raise ValueError("Missing required environment variables: fireflyIII_id and fireflyIII_secret")

fireflyIII = FireflyIII("http://192.168.1.30:8081/", fireflyIII_id, fireflyIII_secret)


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
    
    # Safe config file loading
    try:
        with open('config.json', 'r') as file:
            config = json.load(file)
    except FileNotFoundError:
        return "Error: config.json file not found", 500
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON in config.json: {e}", 500
    except Exception as e:
        return f"Error loading config: {e}", 500

    filePrefix = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    for key, value in request.files.items():
        try:
            fileAccount = request.files[key]
            
            # Validate file extension
            if not fileAccount.filename.lower().endswith(('.csv', '.xlsx')):
                return f"Error: Invalid file type for {key}. Only CSV and XLSX files are allowed.", 400
            
            # Safe file path construction
            safe_filename = f"{filePrefix}_{key}.csv"
            fileAccountPath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
            
            # Ensure the path is within the upload folder
            if not os.path.abspath(fileAccountPath).startswith(os.path.abspath(app.config['UPLOAD_FOLDER'])):
                return "Error: Invalid file path", 400
                
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
            
            # Safe file removal
            try:
                os.remove(fileAccountPath)
            except OSError as e:
                print(f"Warning: Could not remove temporary file {fileAccountPath}: {e}")
            
            accounts.update({key: account})
            
        except Exception as e:
            return f"Error processing file {key}: {e}", 500

    relations = generate_dynamic_relationship(list(accounts.values()))

    print(relations)

    transactions = base_v2.compare_accounts(accounts, relations, config)

    for account in accounts.values():
        try:
            if account.account_type in [AccountType.CHECKING_ACCOUNT, AccountType.PREPAID_CARD]:
                function_name = f"elaborate_{account.account_type.value}_{account.bank.lower()}"
                
                # Validate function exists before calling
                if hasattr(base_v2, function_name):
                    elaborate_single_account = getattr(base_v2, function_name)
                    list_transactions = elaborate_single_account(account, config)
                    transactions.extend(list_transactions)
                else:
                    print(f"Warning: Function {function_name} not found in base_v2")
                    
            elif account.account_type == AccountType.PAYPAL:
                function_name = f"elaborate_{AccountType.PAYPAL.value}"
                
                # Validate function exists before calling
                if hasattr(base_v2, function_name):
                    elaborate_single_account = getattr(base_v2, function_name)
                    list_transactions = elaborate_single_account(account, config)
                    transactions.extend(list_transactions)
                else:
                    print(f"Warning: Function {function_name} not found in base_v2")
        except Exception as e:
            print(f"Error processing account {account.id}: {e}")
            continue
            

    transactions = base_v2.findSourceDestinationCategoryID(transactions, fireflyIII)
    transactionsNotExistend = base_v2.checkExistingTransations(transactions, fireflyIII)
    transactions_dict = listToDict(transactionsNotExistend)

    for account in accounts.values():
        try:
            safe_filename = f"{account.id}.csv"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
            
            # Ensure the path is within the upload folder
            if not os.path.abspath(file_path).startswith(os.path.abspath(app.config['UPLOAD_FOLDER'])):
                print(f"Warning: Invalid file path for account {account.id}")
                continue
                
            account.dataframe.to_csv(file_path, sep=',', encoding='utf-8', index=False, header=True)
        except Exception as e:
            print(f"Error saving dataframe for account {account.id}: {e}")
            continue

    return render_template('list_transaction.html', transactions=transactions_dict, categories=categories)

@app.route('/continue_session', methods=['POST'])
def continue_session():
    if not fireflyIII.checkAccessToken():
        return redirect(fireflyIII.startAuth())
    
    categories = fireflyIII.getCategories()

    filePrefix = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    try:
        previousSessionFile = request.files['previousSessionFile']
        
        # Validate file extension
        if not previousSessionFile.filename.lower().endswith('.csv'):
            return "Error: Invalid file type. Only CSV files are allowed.", 400
        
        # Safe file path construction
        safe_filename = f"{filePrefix}_fileSession.csv"
        previousSessionFilePath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        
        # Ensure the path is within the upload folder
        if not os.path.abspath(previousSessionFilePath).startswith(os.path.abspath(app.config['UPLOAD_FOLDER'])):
            return "Error: Invalid file path", 400
            
        previousSessionFile.save(previousSessionFilePath)

        csvFileSession = pandas.read_csv(previousSessionFilePath)
        
        # Safe file removal
        try:
            os.remove(previousSessionFilePath)
        except OSError as e:
            print(f"Warning: Could not remove temporary file {previousSessionFilePath}: {e}")
            
    except KeyError:
        return "Error: No file uploaded", 400
    except Exception as e:
        return f"Error processing file: {e}", 500

    transactions = base_v2.read_previous_transactions(csvFileSession)

    transactions = base_v2.findSourceDestinationCategoryID(transactions, fireflyIII)

    transactionsNotExistend = base_v2.checkExistingTransations(transactions, fireflyIII)

    transactions_dict = listToDict(transactionsNotExistend)

    return render_template('list_transaction.html', transactions=transactions_dict, categories=categories)
    

@app.route('/oauth2_callback', methods=['GET'])
def oauth2_callback():
    # Get OAuth2 parameters
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    error_description = request.args.get('error_description')
    
    # Handle OAuth2 errors
    if error:
        logger.error(f"OAuth2 error: {error} - {error_description}")
        return f"Authentication error: {error}", 400
    
    if not code:
        logger.error("No authorization code received")
        return "No authorization code received", 400

    result = fireflyIII.continueAuth(code, state)

    print("oauth2_callback: "+str(result))
    
    if result:
        return redirect('/')
    else:
        return "Authentication failed", 400

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
    safe_filename = f"{filePrefix}_fileTransactions.csv"
    fileOutputPath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
    
    # Ensure the path is within the upload folder
    if not os.path.abspath(fileOutputPath).startswith(os.path.abspath(app.config['UPLOAD_FOLDER'])):
        return "Error: Invalid file path", 400
    
    try:
        with open(fileOutputPath, 'w', newline='') as csvfile:
            fieldnames = ['date', 'transactionType', 'sourceAccount', 'destinationAccount', 'description', 'amount', 'category', 'sourceAccountId', 'destinationAccountId']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_rows)
    except Exception as e:
        return f"Error writing file: {e}", 500

    #return str(grouped_data)
    return send_file(fileOutputPath, as_attachment=True)

@app.route('/insert', methods=['POST'])
def insert():

    # Dizionario per raggruppare i dati
    grouped_data = defaultdict(dict)

    # Raggruppamento dei dati
    for key, value in request.form.items():
        try:
            prefix, suffix = key.rsplit('_', 1)
            grouped_data[suffix][prefix] = value
        except ValueError:
            # Skip malformed keys
            continue

    csv_rows = []
    results = []
    for key, value in grouped_data.items():
        csv_rows.append(value)

        # Validate required fields
        required_fields = ['transactionType', 'date', 'amount', 'description']
        for field in required_fields:
            if not value.get(field):
                return f"Error: Missing required field '{field}'", 400

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

        try:
            result = fireflyIII.insertTransactions(data)
            print(result)
            results.append(result)
        except Exception as e:
            print(f"Error inserting transaction: {e}")
            results.append({"error": str(e)})
        #dataJSON = json.dumps(data)

    return json.dumps(results)

if __name__ == "__main__":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    # Validate SSL certificate files exist
    cert_file = 'certs/server.crt'
    key_file = 'certs/server.key'
    
    if not os.path.exists(cert_file):
        print(f"Error: SSL certificate file not found: {cert_file}")
        exit(1)
    
    if not os.path.exists(key_file):
        print(f"Error: SSL key file not found: {key_file}")
        exit(1)
    
    context = (cert_file, key_file)
    app.run(host='0.0.0.0', port=8443, debug=True, ssl_context=context)
