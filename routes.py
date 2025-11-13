"""Route handlers for the Flask application."""
from flask import render_template, request, redirect, send_file, jsonify
from datetime import datetime
import os
import csv
import json
import pandas
from entities.account import AccountType
import base_v2
import banks.normalization as normalization
from helpers import (
    generate_dynamic_relationship,
    listToDict,
    parse_form_grouped,
    csv_rows_from_grouped,
    dataframe_from_grouped,
    build_transactions_context_from_df,
    CSV_FIELDNAMES
)
import banks.banks

def register_routes(app, fireflyIII):
    """Register all routes with the Flask application.
    
    Args:
        app (Flask): Flask application instance to register routes with.
        fireflyIII (FireflyIII): FireflyIII client instance for API calls.
    """
    
    @app.route('/', methods=['GET'])
    def index():
        """Handle the root route.
        
        Checks authentication and renders the session manager page.
        
        Returns:
            Response: Redirect to auth URL if not authenticated, otherwise
                     renders session_manager.html template.
        """
        if not fireflyIII.checkAccessToken():
            return redirect(fireflyIII.startAuth())
        return render_template('session_manager.html')

    @app.route('/new_session', methods=['POST', 'GET'])
    def new_session():
        """Handle new session creation.
        
        Processes uploaded account files, extracts transactions, compares
        accounts, and renders the transaction list page.
        
        Returns:
            Response: Error response if validation fails, otherwise renders
                     list_transaction.html template with transactions and categories.
        """
        if request.method == 'GET':
            return redirect('/')
        
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
                    if hasattr(banks, function_name):
                        elaborate_single_account = getattr(banks, function_name)
                        list_transactions = elaborate_single_account(account, config)
                        transactions.extend(list_transactions)
                    else:
                        print(f"Warning: Function {function_name} not found in base_v2")
                        
                elif account.account_type == AccountType.PAYPAL:
                    function_name = f"elaborate_{AccountType.PAYPAL.value}"
                    
                    # Validate function exists before calling
                    if hasattr(banks, function_name):
                        elaborate_single_account = getattr(banks, function_name)
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

    @app.route('/continue_session', methods=['POST', 'GET'])
    def continue_session():
        """Handle continuing a previous session.
        
        Loads a previously saved session CSV file, processes transactions,
        and renders the transaction list page.
        
        Returns:
            Response: Redirect to root if GET request, error response if
                     validation fails, otherwise renders list_transaction.html
                     template with transactions and categories.
        """
        if request.method == 'GET':
            return redirect('/')
        
        if not fireflyIII.checkAccessToken():
            return redirect(fireflyIII.startAuth())
        
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

        transactions_dict, categories = build_transactions_context_from_df(csvFileSession, fireflyIII)
        return render_template('list_transaction.html', transactions=transactions_dict, categories=categories)
        

    @app.route('/oauth2_callback', methods=['GET'])
    def oauth2_callback():
        """Handle OAuth2 callback from FireflyIII.
        
        Processes the authorization code from FireflyIII OAuth2 flow
        and completes authentication.
        
        Returns:
            Response: Redirect to root page after authentication.
        """
        result = fireflyIII.continueAuth(request.args.get('code'))
        print("oauth2_callback: "+str(result))
        return redirect('/')

    @app.route('/save', methods=['POST'])
    def save():
        """Save transactions to CSV file.
        
        Processes form data, converts to CSV format, and returns the file
        as a download.
        
        Returns:
            Response: Error response if validation fails, otherwise returns
                     CSV file as attachment for download.
        """
        grouped_data = parse_form_grouped(request.form)
        print(grouped_data.items())
        csv_rows = csv_rows_from_grouped(grouped_data)

        filePrefix = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        safe_filename = f"{filePrefix}_fileTransactions.csv"
        fileOutputPath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        
        # Ensure the path is within the upload folder
        if not os.path.abspath(fileOutputPath).startswith(os.path.abspath(app.config['UPLOAD_FOLDER'])):
            return "Error: Invalid file path", 400
        
        try:
            with open(fileOutputPath, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=CSV_FIELDNAMES)
                writer.writeheader()
                writer.writerows(csv_rows)
        except Exception as e:
            return f"Error writing file: {e}", 500

        return send_file(fileOutputPath, as_attachment=True)

    @app.route('/insert', methods=['POST'])
    def insert():
        """Insert transactions into FireflyIII.
        
        Processes form data, validates required fields, resolves account IDs,
        and inserts transactions into FireflyIII via API.
        
        Returns:
            str: JSON string containing results of each transaction insertion,
                including success or error information.
        """
        grouped_data = parse_form_grouped(request.form)

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

            data = {"error_if_duplicate_hash": False, "apply_rules": True, "fire_webhooks": True, "transactions": [fireflyTransaction]}

            try:
                result = fireflyIII.insertTransactions(data)
                print(result)
                results.append(result)
            except Exception as e:
                print(f"Error inserting transaction: {e}")
                results.append({"error": str(e)})

        return json.dumps(results)

    @app.route('/reprocess', methods=['POST'])
    def reprocess():
        """Reprocess transactions from the list transaction table.
        
        Takes current form data, rebuilds transactions, re-runs enrichment
        and duplicate checks, and re-renders the transaction list.
        
        Returns:
            Response: Redirect to auth URL if not authenticated, otherwise
                     renders list_transaction.html template with updated
                     transactions and categories.
        """
        if not fireflyIII.checkAccessToken():
            return redirect(fireflyIII.startAuth())

        grouped_data = parse_form_grouped(request.form)
        df = dataframe_from_grouped(grouped_data)
        transactions_dict, categories = build_transactions_context_from_df(df, fireflyIII)
        return render_template('list_transaction.html', transactions=transactions_dict, categories=categories)

    @app.route('/api/banks_with_checking_account')
    def banks_with_checking_account():
        import json
        with open('config.json') as f:
            config = json.load(f)
        banks = []
        for bank in config:
            if 'checking_account' in config[bank]:
                banks.append({'id': bank, 'friendly_name': config[bank].get('friendly_name', bank)})
        #banks = [bank for bank in config if 'checking_account' in config[bank]]
        return jsonify(banks)
    
    @app.route('/api/banks_with_prepaid_account')
    def banks_with_prepaid_account():
        import json
        with open('config.json') as f:
            config = json.load(f)
        banks = []
        for bank in config: 
            if 'prepaid_card' in config[bank]:
                banks.append({'id': bank, 'friendly_name': config[bank].get('friendly_name', bank)})
        #banks = [bank for bank in config if 'prepaid_card' in config[bank]]
        return jsonify(banks)