# This file is part of Aequora.
#
# Aequora is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Aequora is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Aequora.  If not, see <https://www.gnu.org/licenses/>.
import re
import pandas
from datetime import datetime
from entities.account import Account, AccountType
from entities.transaction import FinancialTransaction, TransactionType
import compute_next_business_day
import banks.banks

def get_account_from_key(key, request):
    """Get Account object from form key and request data.
    
    Creates an Account object from the key and extracts additional
    information (bank, associated account) from the request form.
    
    Args:
        key (str): Account key from form (e.g., 'checkingAccount_1').
        request (Request): Flask request object containing form data.
        
    Returns:
        Account: Configured Account object with bank and association set.
    """
    account = Account(key)

    if account.account_type == AccountType.DEBIT_CARD:
        id_parts = key.split("_")
        associated_id = request.form[f"debitCard_association_{id_parts[1]}"]
        account.setAssociation(associated_id)
    elif account.account_type in [AccountType.CHECKING_ACCOUNT, AccountType.PREPAID_CARD]:
        bank = request.form[f"{key}_bank"]
        account.setBank(bank)

    return account

def get_dataset(account, file_path, config, associated_bank=None):
    """Load account transaction data from file into pandas DataFrame.
    
    Reads CSV or XLSX file based on account type and configuration,
    using appropriate pandas read parameters from config.
    
    Args:
        account (Account): Account object containing account type information.
        file_path (str): Path to the transaction data file.
        config (dict): Configuration dictionary with file format and read parameters.
        associated_bank (str, optional): Bank name for associated accounts
                                        (e.g., for debit cards). Defaults to None.
        
    Returns:
        pandas.DataFrame: DataFrame containing transaction data from the file.
    """
    if account.account_type == AccountType.PAYPAL:
        if config["PayPal"]['file_extension'] == "csv":
            read_params = {"filepath_or_buffer": file_path}
        elif config["PayPal"]['file_extension'] == "xlsx":
            read_params = {"io": file_path}
        read_params.update(config["PayPal"]['pandas_read_params'])
    else:
        bank = associated_bank or account.bank
        if config[bank][account.account_type.value]['file_extension'] == "csv":
            read_params = {"filepath_or_buffer": file_path}
        elif config[bank][account.account_type.value]['file_extension'] == "xlsx":
            read_params = {"io": file_path}
        read_params.update(config[bank][account.account_type.value]['pandas_read_params'])

    if account.account_type == AccountType.PAYPAL:
        if config["PayPal"]['file_extension'] == "csv":
            df = pandas.read_csv(**read_params)
        elif config["PayPal"]['file_extension'] == "xlsx":
            df = pandas.read_excel(**read_params)
    else:
        if config[bank][account.account_type.value]['file_extension'] == "csv":
            df = pandas.read_csv(**read_params)
        elif config[bank][account.account_type.value]['file_extension'] == "xlsx":
            df = pandas.read_excel(**read_params)

    return df

def get_normalization_function(account, config, normalization, associated_bank=None):
    """Get normalization function for account data processing.
    
    Retrieves the normalization function name from config and returns
    the corresponding function from the normalization module.
    
    Args:
        account (Account): Account object containing account type information.
        config (dict): Configuration dictionary with normalization function names.
        normalization (module): Normalization module containing functions.
        associated_bank (str, optional): Bank name for associated accounts.
                                        Defaults to None.
        
    Returns:
        function or None: Normalization function if found in config, None otherwise.
    """
    if account.account_type == AccountType.PAYPAL:
        norm_fn_name = config["PayPal"].get('normalizationFunction')
    else:
        bank = associated_bank or account.bank
        norm_fn_name = config[bank][account.account_type.value].get('normalizationFunction')

    return getattr(normalization, norm_fn_name) if norm_fn_name else None

def process_dataframe(df, normalization_fn):
    """Process DataFrame by applying normalization and adding Found column.
    
    Applies normalization function if provided and adds a 'Found' column
    initialized to False for tracking matched transactions.
    
    Args:
        df (pandas.DataFrame): DataFrame to process.
        normalization_fn (function or None): Normalization function to apply.
        
    Returns:
        pandas.DataFrame: Processed DataFrame with 'Found' column added.
    """
    if normalization_fn:
        normalization_fn(df)
    df["Found"] = False
    return df

def read_previous_transactions(csvFileSession):
    """Read transactions from a CSV session DataFrame.
    
    Parses a pandas DataFrame containing previously saved transaction data
    and creates FinancialTransaction objects.
    
    Args:
        csvFileSession (pandas.DataFrame): DataFrame with columns for date,
                                         transactionType, sourceAccount,
                                         destinationAccount, description,
                                         amount, and category.
        
    Returns:
        list: List of FinancialTransaction objects.
    """
    transactions = []

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
        
        if not pandas.isna(lineSession[7]):
            financialTransaction.setCategoryID(lineSession[7])

        transactions.append(financialTransaction)
    
    return transactions    

def compare_accounts(accounts, relationships, config):
    """Compare transactions between related accounts to find matches.
    
    Matches transactions between related accounts based on amount, date,
    and description patterns. Marks matched transactions as 'Found' in
    the account DataFrames.
    
    Args:
        accounts (dict): Dictionary of Account objects keyed by account ID.
        relationships (list): List of tuples (account1_id, account2_id, [day_offsets])
                           representing valid relationships.
        config (dict): Configuration dictionary with field mappings.
        
    Returns:
        list: List of FinancialTransaction objects representing matched transactions.
    """
    transactions = []
    index_dict = 0

    for relationship in relationships:
        print(accounts.get(relationship[0]).account_type.value+" "+accounts.get(relationship[1]).account_type.value)
        a1 = accounts.get(relationship[0])
        a2 = accounts.get(relationship[1])
        
        # Validate accounts exist
        if not a1 or not a2:
            print(f"Warning: Account not found in relationship {relationship}")
            continue
            
        if a1.account_type ==  AccountType.PAYPAL:
            fields_a1 = config.get("PayPal", {}).get('fields')
            bank_a1 = "PayPal"
        elif a1.account_type ==  AccountType.DEBIT_CARD:
            associated_account = accounts.get(a1.id_associated_account)
            if not associated_account:
                print(f"Warning: Associated account not found for {a1.id_associated_account}")
                continue
            fields_a1 = config.get(associated_account.bank, {}).get(a1.account_type.value, {}).get('fields')
            bank_a1 = associated_account.bank
        else:
            fields_a1 = config.get(a1.bank, {}).get(a1.account_type.value, {}).get('fields')
            bank_a1 = a1.bank
            
        fields_a2 = config.get(a2.bank, {}).get(a2.account_type.value, {}).get('fields')
        
        # Validate fields configuration
        if not fields_a1 or not fields_a2:
            print(f"Warning: Missing fields configuration for accounts")
            continue


        indexesToDrop_a1 = []
        indexesToDrop_a2 = []
        for transaction_a1 in a1.dataframe.itertuples():
            found = False
            amount_a1 = transaction_a1[fields_a1.get('amount')]
            date_a1 = transaction_a1[fields_a1.get('date')]
            destination_a1 = transaction_a1[fields_a1.get('destination')]
            if fields_a1.get('time'):
                time_a1 = transaction_a1[fields_a1.get('time')]
            if fields_a1.get('source'):
                source_a1 = transaction_a1[fields_a1.get('source')]

            for transaction_a2 in a2.dataframe.itertuples():
                # Safer way to check if transaction is found
                found_index = None
                try:
                    found_index = a2.dataframe.columns.get_loc("Found")
                    is_found = transaction_a2[found_index + 1]  # +1 because itertuples() adds index
                except (KeyError, IndexError):
                    # If "Found" column doesn't exist, assume not found
                    is_found = False
                
                if is_found == False:
                    amount_a2 = transaction_a2[fields_a2.get('amount')]
                    date_a2 = transaction_a2[fields_a2.get('date')]
                    destination_a2 = transaction_a2[fields_a2.get('destination')]
                    if fields_a2.get('time'):
                        time_a2 = transaction_a2[fields_a2.get('time')]
                    if fields_a2.get('source'):
                        source_a2 = transaction_a2[fields_a2.get('source')]

                    for daysNumber in relationship[2]:
                        # Validate date types before comparison
                        try:
                            date_a1_py = date_a1.to_pydatetime() if hasattr(date_a1, 'to_pydatetime') else date_a1
                            date_a2_py = date_a2.to_pydatetime() if hasattr(date_a2, 'to_pydatetime') else date_a2
                            
                            next_business_day = compute_next_business_day.next_number_business_day(date_a1_py, 'IT', daysNumber)
                            #print(f"Comparing transactions: A1 Date {date_a1_py}, A2 Date {date_a2_py}, Next Business Day {next_business_day}, Amount A1 {amount_a1}, Amount A2 {amount_a2}")
                            #print(f"abs(amount_a1) == abs(amount_a2): {abs(amount_a1) == abs(amount_a2)}, next_business_day == date_a2_py: {next_business_day == date_a2_py}")
                            
                            if abs(amount_a1) == abs(amount_a2) and next_business_day == date_a2_py:
                                #print(f"Potential match found between accounts {a1.id} and {a2.id} for amounts {amount_a1} and {amount_a2} on dates {date_a1_py} and {date_a2_py}")
                                
                                if (a1.account_type == AccountType.DEBIT_CARD and a2.account_type == AccountType.CHECKING_ACCOUNT) or (a1.account_type == AccountType.CHECKING_ACCOUNT and a2.account_type == AccountType.DEBIT_CARD):
                                    descPartsA1 = re.split(r'\s{2,}', destination_a1)
                                    descPartsA2 = re.split(r'\s{2,}', destination_a2)

                                    if (len(descPartsA1) > 0 and len(descPartsA2) > 3 and descPartsA1[0] == descPartsA2[3]) or (len(descPartsA1) > 0 and len(descPartsA2) > 4 and descPartsA1[0] == descPartsA2[4]):
                                        if amount_a1 > 0:
                                            transactionType = TransactionType.DEPOSIT
                                            sourceAccount = descPartsA1[0]
                                            destinationAccount = bank_a1
                                        else:
                                            transactionType = TransactionType.WITHDRAWAL
                                            destinationAccount = descPartsA1[0]
                                            sourceAccount = bank_a1

                                        if time_a1:
                                            date_a1 = date_a1.replace(hour=time_a1.hour, minute=time_a1.minute)
                                        elif time_a2:
                                            date_a1 = date_a1.replace(hour=time_a2.hour, minute=time_a2.minute)
                                        
                                        transaction = FinancialTransaction(
                                            transaction_type=transactionType,
                                            date=date_a1,
                                            currency_code="EUR",
                                            amount=abs(amount_a1),
                                            source_account=sourceAccount,
                                            destination_account=destinationAccount
                                        )

                                        transactions.append(transaction)
                                        index_dict += 1

                                        indexesToDrop_a1.append(transaction_a1[0])
                                        indexesToDrop_a2.append(transaction_a2[0])
                                        found = True
                                        a1.dataframe.at[transaction_a1[0], "Found"] = True
                                        a2.dataframe.at[transaction_a2[0], "Found"] = True
                                
                                elif (a1.account_type in [AccountType.DEBIT_CARD, AccountType.CHECKING_ACCOUNT, AccountType.PREPAID_CARD] and a2.account_type == AccountType.PAYPAL) or (a1.account_type == AccountType.PAYPAL and a2.account_type in [AccountType.DEBIT_CARD, AccountType.CHECKING_ACCOUNT, AccountType.PREPAID_CARD]):
                                    if a1.account_type == AccountType.PAYPAL:
                                        source = source_a1
                                        destination = destination_a1
                                        bank_secondAccount = accounts.get(a2.id_associated_account).bank if a2.account_type == AccountType.DEBIT_CARD else a2.bank
                                        destination_secondAccount = destination_a2
                                        date = date_a1.replace(hour=time_a1.hour, minute=time_a1.minute)
                                    elif a2.account_type == AccountType.PAYPAL:
                                        source = source_a2
                                        destination = destination_a2
                                        destination_secondAccount = destination_a1
                                        bank_secondAccount = accounts.get(a1.id_associated_account).bank if a1.account_type == AccountType.DEBIT_CARD else a1.bank
                                        date = date_a2.replace(hour=time_a2.hour, minute=time_a2.minute)

                                    #print(f"Comparing source '{source}' with bank '{bank_secondAccount}'")
                                    #print(f"Comparing source '{source}' with destination second account '{destination_secondAccount}'")

                                    #if source.lower().find(bank_secondAccount.lower()) > -1:
                                    if destination_secondAccount.lower().find(source.lower()) > -1:
                                        if amount_a1 > 0:
                                            transactionType = TransactionType.DEPOSIT
                                            sourceAccount = destination
                                            destinationAccount = bank_secondAccount
                                        else:
                                            transactionType = TransactionType.WITHDRAWAL
                                            destinationAccount = destination
                                            sourceAccount = bank_secondAccount
                                        #print(f"Creating transaction on compare_accounts: {transactionType} of {abs(amount_a1)} EUR on {date} from {sourceAccount} to {destinationAccount}")
                                        transaction = FinancialTransaction(
                                            transaction_type=transactionType,
                                            date=date,
                                            currency_code="EUR",
                                            amount=abs(amount_a1),
                                            source_account=sourceAccount,
                                            destination_account=destinationAccount
                                        )

                                        transactions.append(transaction)
                                        index_dict += 1

                                        found = True
                                        indexesToDrop_a1.append(transaction_a1[0])
                                        indexesToDrop_a2.append(transaction_a2[0])
                                        a1.dataframe.at[transaction_a1[0], "Found"] = True
                                        a2.dataframe.at[transaction_a2[0], "Found"] = True

                                        break
                        except Exception as e:
                            print(f"Error processing transaction comparison: {e}")
                            continue
                    if found:
                        break
    
    return transactions

def findSourceDestinationCategoryID(transactions, fireflyIII):
    """Find and set source, destination, and category IDs for transactions.
    
    Enriches transactions by finding matching accounts in FireflyIII
    and setting account IDs. Also attempts to set category IDs based
    on counterparty account history.
    
    Args:
        transactions (list): List of FinancialTransaction objects to enrich.
        fireflyIII (FireflyIII): FireflyIII client instance for API calls.
        
    Returns:
        list: List of enriched FinancialTransaction objects with IDs set.
    """
    list_transactions = []
    for transaction in transactions:
        sourceAccount = transaction.source_account
        #if pandas.isna(sourceAccount):
            #sourceAccount = ""
        sourceAccountsFirefly = fireflyIII.autocompleteAccounts(sourceAccount, "Revenue account")
        if len(sourceAccountsFirefly) > 0:
            transaction.setSourceAccountID(sourceAccountsFirefly[0].get('id'))
        
        destinationAccount = transaction.destination_account
        #if pandas.isna(destinationAccount):
        #    destinationAccount = ""
        destinationAccountsFirefly = fireflyIII.autocompleteAccounts(destinationAccount, "Expense account")
        if len(destinationAccountsFirefly) > 0:
            transaction.setDestinationAccountID(destinationAccountsFirefly[0].get('id'))

        if not hasattr(transaction, 'category_id'):
            accountCounterpartyID = transaction.getCounterpartyAccount().get('id')
            if accountCounterpartyID is not None:
                accountTransactions = fireflyIII.getTransactionsOfAccount(accountCounterpartyID)
                transaction.setCategoryID(getMostUsedCategoryID(accountTransactions))
        
        list_transactions.append(transaction)
    
    return list_transactions

def getMostUsedCategoryID(accountTransaction):
    """Get the most frequently used category ID from account transactions.
    
    Analyzes transaction history for an account and returns the category
    ID that appears most frequently.
    
    Args:
        accountTransaction (dict): FireflyIII API response containing account
                                  transaction data.
        
    Returns:
        int: Most frequently used category ID, or -1 if no categories found.
    """
    categories = {}
    try:
        if "data" in accountTransaction and isinstance(accountTransaction.get('data'), list):
            for singleData in accountTransaction.get('data'):
                if isinstance(singleData, dict) and 'attributes' in singleData:
                    transactions = singleData.get('attributes', {}).get('transactions', [])
                    if isinstance(transactions, list):
                        for transaction in transactions:
                            if isinstance(transaction, dict):
                                category_id = transaction.get('category_id')
                                if category_id is not None:
                                    if category_id in categories:
                                        categories[category_id] = categories[category_id] + 1
                                    else:
                                        categories[category_id] = 1
    except Exception as e:
        print(f"Error processing account transactions: {e}")
        return -1
        
    if len(categories) > 0:
        return max(categories, key=categories.get)
    else:
        return -1

def checkExistingTransations(sourceTransations, fireflyIII):
    """Check which transactions already exist in FireflyIII.
    
    Searches FireflyIII for existing transactions and filters out
    duplicates, returning only transactions that don't exist yet.
    
    Args:
        sourceTransations (list): List of FinancialTransaction objects to check.
        fireflyIII (FireflyIII): FireflyIII client instance for API calls.
        
    Returns:
        list: List of FinancialTransaction objects that don't exist in FireflyIII.
    """
    if not sourceTransations:
        return []
        
    transactionsSorted = sorted(sourceTransations, key=lambda x: (x.date, x.amount))

    transactionsNotExistentTemp = []
    j = 0

    while j < len(transactionsSorted):
        try:
            bank_account = transactionsSorted[j].getBankAccount()
            fireflyAssetId = bank_account.get("id") if bank_account else None
            if fireflyAssetId is None:
                fireflyAssetId = 1
                
            query = "account_id:"+str(fireflyAssetId)+" amount:"+('{:.2f}'.format(transactionsSorted[j].amount))+" date_on:"+transactionsSorted[j].date.strftime('%Y-%m-%d')
            
            goNext = True
            k = j + 1
            n = 1
            
            # Check if there are identical transactions
            if k < len(transactionsSorted):
                while goNext and k < len(transactionsSorted):
                    if (transactionsSorted[j].amount == transactionsSorted[k].amount) and (transactionsSorted[j].date.strftime('%Y-%m-%d') == transactionsSorted[k].date.strftime('%Y-%m-%d')) and (transactionsSorted[j].transaction_type == transactionsSorted[k].transaction_type):
                        n += 1
                        goNext = True
                    else:
                        goNext = False
                    
                    k += 1
            
            result = fireflyIII.searchTransations(query)
            # If these identical transactions are not in financial manager, it check if they are stored as a single transaction 
            if len(result.get("data", [])) != n:
                query = "account_id:"+str(fireflyAssetId)+" amount:"+('{:.2f}'.format(transactionsSorted[j].amount * n))+" date_on:"+transactionsSorted[j].date.strftime('%Y-%m-%d')

                result = fireflyIII.searchTransations(query)

                # If the single transaction does not exist, these identical transaction are added to the list of non-existent transactions
                if len(result.get("data", [])) != 1:
                    for z in range(j, j+n):
                        if z < len(transactionsSorted):
                            transactionsNotExistentTemp.append(transactionsSorted[z])

            j += n
        except Exception as e:
            print(f"Error processing transaction at index {j}: {e}")
            j += 1

    transactionsNotExistent = []
    transactionStoredToExclude = ""
    # Check if the transaction are stored with parts
    for transaction in transactionsNotExistentTemp:
        try:
            counterparty_account = transaction.getCounterpartyAccount()
            if not counterparty_account:
                transactionsNotExistent.append(transaction)
                continue
                
            query = "account_id:"+str(counterparty_account.get("id"))+" date_on:"+transaction.date.strftime('%Y-%m-%d')+transactionStoredToExclude

            result = fireflyIII.searchTransations(query)

            if len(result.get("data", [])) > 0:
                
                for storedTransaction in result.get("data", []):
                    transactionStoredAmount = 0
                    try:
                        transactions_parts = storedTransaction.get("attributes", {}).get("transactions", [])
                        for part in transactions_parts:
                            if isinstance(part, dict):
                                amount = part.get("amount")
                                if amount is not None:
                                    transactionStoredAmount += float(amount)
                    except (ValueError, TypeError) as e:
                        print(f"Error processing transaction amount: {e}")
                        transactionStoredAmount = 0
                    if transaction.amount != transactionStoredAmount:
                        transactionsNotExistent.append(transaction)
                    else:
                        transactionStoredToExclude += " -id:"+str(storedTransaction.get("id"))
            else:
                transactionsNotExistent.append(transaction)
        except Exception as e:
            print(f"Error processing transaction: {e}")
            transactionsNotExistent.append(transaction)

    return transactionsNotExistent