from enum import Enum

# Enum per la tipologia di transazione
class TransactionType(Enum):
    DEPOSIT = "deposit"
    DEBIT = "debit"

class FinancialTransaction:
    def __init__(self, transaction_type, date, currency_code, amount, source_account, destination_account, category):
        self.transaction_type = self._validate_transaction_type(transaction_type)
        self.date = self._validate_date(date)
        self.currency_code = currency_code.upper()  
        self.amount = amount
        self.source_account = source_account
        self.destination_account = destination_account
        self.category = category

    def _validate_transaction_type(self, transaction_type):
        if isinstance(transaction_type, TransactionType):
            return transaction_type
        elif isinstance(transaction_type, str):
            try:
                return TransactionType(transaction_type.lower())
            except ValueError:
                raise ValueError(f"Invalid transaction type. Choose between: {[t.value for t in TransactionType]}")
        else:
            raise TypeError("Transaction type must be a TransactionType enum or a valid string.")
