from enum import Enum

# Enum per la tipologia di transazione
class TransactionType(Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"

class FinancialTransaction:

    description = ""

    def __init__(self, transaction_type, date, currency_code, amount, source_account, destination_account):
        self.transaction_type = self._validate_transaction_type(transaction_type)
        self.date = date
        self.currency_code = currency_code.upper()  
        self.amount = amount
        self.source_account = source_account
        self.destination_account = destination_account
        #self.category = category
        self.destination_account_id = None
        self.source_account_id = None

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
        
    def setDescription(self, description):
        self.description = description

    def setSourceAccountID(self, sourceAccountID):
        self.source_account_id = sourceAccountID

    def setDestinationAccountID(self, destinationAccountID):
        self.destination_account_id = destinationAccountID

    def setCategoryID(self, categoryID):
        self.category_id = str(int(float(categoryID)))

    def getHTMLDate(self):
        return self.date.strftime('%Y-%m-%dT%H:%M')
    
    def getAccountCounterparty(self, bankAccount):
        if bankAccount == self.source_account:
            return {"id": self.destination_account_id if self.destination_account_id is not None else "", "name": self.destination_account}
            #return self.destination_account
        else:
            return {"id": self.source_account_id if self.source_account_id is not None else "", "name": self.source_account}
            #return self.source_account

    def __str__(self):
        return (
            f"Transaction({self.transaction_type.value}, Date: {self.date.strftime('%Y-%m-%d %H:%M')}, "
            f"Currency: {self.currency_code}, Amount: {self.amount:.2f}, "
            f"From: {self.source_account}, To: {self.destination_account}, "
            f"Description: {self.description} )"
            #f"Category: {self.category})"
        )
    
    def __repr__(self):
        return (
            f"Transaction({self.transaction_type.value}, Date: {self.date.strftime('%Y-%m-%d %H:%M')}, "
            f"Currency: {self.currency_code}, Amount: {self.amount:.2f}, "
            f"From: {self.source_account}, To: {self.destination_account}, "
            f"Description: {self.description} )"
            #f"Category: {self.category})"
        )