This project is licensed under the GNU Affero General Public License v3.0 (AGPLv3).
See the LICENSE file for details.

# Aequora - Transaction Importer

A modular Flask-based web application for importing and processing financial transactions from multiple bank accounts and payment providers into personal finance managers. Currently supports integration with [FireflyIII](https://www.firefly-iii.org/), with extensible architecture for additional finance managers.

## Features

- **Multi-Bank Support**: Import transactions from various banks and payment providers (Unicredit, PayPal, PostePay, Revolut, etc.)
- **Automatic Transaction Matching**: Intelligently matches transactions across different accounts (e.g., debit card and checking account)
- **Duplicate Detection**: Automatically filters out transactions that already exist in FireflyIII
- **Category Suggestions**: Automatically suggests categories based on counterparty account history
- **Account Resolution**: Automatically resolves account names to FireflyIII account IDs
- **Session Management**: Save and continue working on transaction imports
- **Reprocessing**: Re-run transaction enrichment and duplicate checks on existing data
- **Modern Web Interface**: Clean, responsive UI for managing transaction imports

## Project Structure

This project follows a modular architecture for maintainability and extensibility:

```
import_transaction/
├── app.py                      # Main application entry point
├── config.py                   # Flask app and FireflyIII initialization
├── routes.py                   # Route handlers for all endpoints
├── helpers.py                  # Utility functions for form processing and data transformation
├── base_v2.py                  # Core transaction processing logic
├── firefly_iii.py              # FireflyIII API client with OAuth2 authentication
├── normalization.py            # Data normalization functions
├── compute_next_business_day.py # Business day calculation utilities
│
├── entities/                   # Domain model classes
│   ├── __init__.py
│   ├── account.py              # Account entity and AccountType enum
│   └── transaction.py          # FinancialTransaction entity and TransactionType enum
│
├── banks/                      # Bank-specific transaction processors
│   ├── __init__.py
│   ├── unicredit.py            # Unicredit bank transaction processor
│   ├── paypal.py               # PayPal transaction processor
│   ├── postepay.py             # PostePay prepaid card processor
│   └── revolut_it.py           # Revolut Italia processor
│
├── templates/                  # HTML templates
│   ├── session_manager.html    # Main session management interface
│   └── list_transaction.html   # Transaction list and editing interface
│
├── banks.json                 # Bank configuration and field mappings
├── certs/                      # SSL certificates for HTTPS
└── upload/                     # Temporary file upload directory
```

### Modularity Highlights

- **Separation of Concerns**: Configuration, routes, business logic, and data models are separated into distinct modules
- **Bank-Specific Processors**: Each bank/provider has its own processor module in the `banks/` folder, making it easy to add new banks
- **Entity Models**: Domain models are isolated in the `entities/` package
- **Helper Functions**: Reusable utility functions are centralized in `helpers.py`
- **Configuration-Driven**: Bank-specific settings (field mappings, file formats) are defined in `banks.json`

#### Transaction Processing Pipeline

1. **File Input** → Bank-specific file format (CSV/XLSX)
2. **Data Loading** → Pandas DataFrame using `banks.json` parameters
3. **Normalization** → Bank-specific normalization functions
4. **Account Matching** → Cross-account transaction matching
5. **Transaction Extraction** → Bank-specific pattern recognition
6. **Enrichment** → Account ID resolution and category suggestion
7. **Deduplication** → FireflyIII duplicate checking
8. **User Review** → Editable transaction list
9. **Export/Insert** → CSV export or FireflyIII API insertion

#### Account Types
- **Checking Account**: Traditional bank accounts
- **Debit Card**: Linked to a checking account
- **Prepaid Card**: Standalone prepaid cards (e.g., PostePay)
- **PayPal**: PayPal accounts

#### Transaction Types
- **Deposit**: Money coming into an account
- **Withdrawal**: Money going out of an account
- **Transfer**: Money moving between accounts

## Prerequisites

- Python 3.7 or higher
- FireflyIII instance (self-hosted or cloud)
- SSL certificates for HTTPS (required for OAuth2)
- Environment variables:
  - `fireflyIII_id`: OAuth2 client ID from FireflyIII
  - `fireflyIII_secret`: OAuth2 client secret from FireflyIII
  - `fireflyIII_url`: The URL of your FireflyIII instance

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd import_transaction
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install flask pandas openpyxl python-dateutil holidays oauthlib requests
   ```

4. **Set up SSL certificates**:
   - Place your SSL certificate and key in the `certs/` directory:
     - `certs/server.crt`
     - `certs/server.key`

5. **Configure environment variables**:
   ```bash
   export fireflyIII_id="your_client_id"
   export fireflyIII_secret="your_client_secret"
   export fireflyIII_url="https://your-fireflyiii-instance.com"
   ```

6. **Configure FireflyIII OAuth2**:
   - In your FireflyIII instance, create a new OAuth2 client
   - Set the redirect URI to: `https://your-domain:8443/oauth2_callback`
   - Copy the client ID and secret to your environment variables

## Configuration

The `banks.json` file defines how to process files from different banks and payment providers. Each bank/provider entry contains:

- **friendly_name**: Display name for the bank
- **file_extension**: Supported file format (`csv` or `xlsx`)
- **pandas_read_params**: Parameters for reading the file (separator, date formats, etc.)
- **normalizationFunction**: Optional function name for data normalization
- **fields**: Column indices mapping for:
  - `amount`: Transaction amount column
  - `date`: Transaction date column
  - `time`: Transaction time column (optional)
  - `destination`: Destination/description column
  - `source`: Source column (optional)

### Example Configuration

```json
{
    "unicredit": {
        "friendly_name": "Unicredit",
        "checking_account": {
            "file_extension": "csv",
            "pandas_read_params": {
                "decimal": ",",
                "sep": ";",
                "parse_dates": [0, 1],
                "dayfirst": true
            },
            "normalizationFunction": "normalizeUnicredit",
            "fields": {
                "amount": 4,
                "date": 2,
                "destination": 3
            }
        }
    }
}
```

To add a new bank, simply add a new entry to `banks.json` following the same structure, and create a corresponding processor function in the `banks/` folder.

## Usage

### Starting the Application

1. **Activate your virtual environment** (if using one):
   ```bash
   source venv/bin/activate
   ```
2. **Run the application**:
   ```bash
   python app.py
   ```
3. **Access the web interface**:
   - Open your browser and navigate to: `https://localhost:8443`
   - Accept the SSL certificate warning (if using self-signed certificates)

The application will:
- Run on `https://0.0.0.0:8443`
- Enable debug mode
- Use SSL certificates from `certs/` directory
- Display detailed error messages

For production, consider using a WSGI server like Gunicorn:
```bash
gunicorn --bind 0.0.0.0:8443 --certfile certs/server.crt --keyfile certs/server.key app:app
```
**Note**: The application requires HTTPS for OAuth2 to work properly. Ensure your SSL certificates are valid and properly configured.

### New Session Workflow

The **New Session** function processes uploaded bank files and extracts transactions:

#### Workflow Steps

1. **File Upload**:
   - Upload one or more account files (CSV or XLSX) from your banks
   - For each account, specify:
     - Account type (checking account, debit card, prepaid card, PayPal)
     - Bank name (for checking accounts and prepaid cards)
     - Associated account (for debit cards)
2. **File Processing**:
   - Files are validated and temporarily saved
   - Each file is read using bank-specific configuration from `banks.json`
   - Data normalization is applied (if configured)
   - A "Found" flag column is added to track matched transactions
3. **Account Relationship Generation**:
   - The system automatically generates relationships between accounts:
     - Debit cards → Associated checking accounts
     - PayPal → Checking accounts or prepaid cards
     - Prepaid cards → Checking accounts
   - These relationships define how transactions are matched across accounts
4. **Transaction Matching**:
   - Transactions are compared between related accounts
   - Matches are identified based on:
     - Amount (absolute value)
     - Date (with configurable day offsets)
     - Description patterns
   - Matched transactions are marked as "Found" to avoid duplicate processing
5. **Single Account Processing**:
   - For each account, bank-specific processors analyze unmatched transactions
   - Transaction types are identified based on description patterns:
     - Withdrawals (e.g., "PRELIEVO", "PAGAMENTO")
     - Deposits (e.g., "BONIFICO A VOSTRO FAVORE", "VERSAMENTO")
     - Transfers
   - FinancialTransaction objects are created for each identified transaction
6. **Enrichment**:
   - Source and destination accounts are resolved to FireflyIII account IDs using autocomplete
   - Categories are suggested based on counterparty account transaction history
   - The most frequently used category for each counterparty is assigned
7. **Duplicate Checking**:
   - All transactions are checked against existing FireflyIII transactions
   - Duplicates are filtered out based on:
     - Account ID
     - Amount
     - Date
     - Transaction type
8. **Display**:
   - The transaction list is displayed in an editable table
   - Users can modify:
     - Transaction type
     - Source and destination accounts
     - Description
     - Amount
     - Category
   - Account dataframes are saved to CSV files for later use

### Continue Session Workflow

The **Continue Session** function allows you to resume work on a previously saved session:

1. **File Upload**:
   - Upload a CSV file that was previously exported using the "Esporta CSV" button
   - The file contains all transaction data from a previous session
2. **Transaction Reconstruction**:
   - Transactions are read from the CSV file
   - FinancialTransaction objects are recreated with all saved data
3. **Re-enrichment**:
   - Source and destination account IDs are resolved again
   - Categories are re-suggested based on current FireflyIII data
   - Duplicate checking is performed again
4. **Display**:
   - The transaction list is displayed with updated information
   - Users can make further edits and save or insert transactions

### Reprocess Function

The **Reprocess** button allows you to re-run enrichment and duplicate checking on the current transaction list without re-uploading files:

1. Current form data is collected
2. Transactions are rebuilt from the form data
3. Enrichment and duplicate checking are re-executed
4. The page is refreshed with updated transaction information

### Exporting and Inserting Transactions

- **Export CSV**: Downloads all transactions as a CSV file for backup or later use
- **Insert**: Sends all transactions to FireflyIII via the API
  - Account IDs are resolved if not already set
  - Transactions are created with categories and rules applied
  - Results are returned as JSON

## Support and Contributing

### Getting Help

If you encounter issues or have questions:

1. **Check the Configuration**: Ensure `banks.json` is properly formatted and matches your bank file structure
2. **Verify Environment Variables**: Confirm that `fireflyIII_id` and `fireflyIII_secret` are set correctly
3. **Check SSL Certificates**: Ensure `certs/server.crt` and `certs/server.key` exist and are valid
4. **Review Logs**: Check console output for error messages and warnings

### Reporting Issues

When reporting issues, please include:

- Python version
- Operating system
- Error messages or stack traces
- Steps to reproduce the issue
- Sample file structure (without sensitive data)
- Relevant configuration from `banks.json`

### Contributing

Contributions are welcome! To contribute:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/new-bank-support`
3. **Add your changes**:
   - For new banks: Add configuration to `banks.json` and create a processor in `banks/`
   - For bug fixes: Ensure backward compatibility
   - Follow existing code style and add docstrings
4. **Test your changes**: Verify that existing functionality still works
5. **Submit a pull request**: Include a description of your changes

### Adding Support for a New Bank

To add support for a new bank:

1. **Add configuration** to `banks.json`:
   ```json
   "new_bank": {
       "friendly_name": "New Bank",
       "checking_account": {
           "file_extension": "csv",
           "pandas_read_params": { ... },
           "fields": { ... }
       }
   }
   ```

2. **Create a processor** in `banks/new_bank.py`:
   ```python
   def elaborate_checking_account_new_bank(account, config):
       # Process transactions based on description patterns
       # Return list of FinancialTransaction objects
   ```

3. **Export the function** in `banks/__init__.py` or import it in `base_v2.py`

4. **Test** with sample files from the new bank

### Code Style

- Follow PEP 8 Python style guide
- Add docstrings to all functions (following the existing format)
- Use type hints where appropriate
- Keep functions focused and modular
- Add comments for complex logic

## License

[Specify your license here]

## Acknowledgments

- Built for integration with [FireflyIII](https://www.firefly-iii.org/)
- Uses Flask for the web framework
- Pandas for data processing

