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
from enum import Enum

# Enum per la tipologia di transazione
class TransactionType(Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"

class FinancialTransaction:

    description = ""

    def __init__(self, transaction_type, date, currency_code, amount, source_account, destination_account):
        """Initialize a FinancialTransaction object.
        
        Args:
            transaction_type (TransactionType or str): Type of transaction
                (deposit, withdrawal, or transfer).
            date (datetime): Date and time of the transaction.
            currency_code (str): Currency code (e.g., 'EUR').
            amount (float or str): Transaction amount.
            source_account (str): Name of the source account.
            destination_account (str): Name of the destination account.
        """
        self.transaction_type = self._validate_transaction_type(transaction_type)
        self.date = date
        self.currency_code = currency_code.upper()  
        self.amount = float(amount)
        self.source_account = source_account
        self.destination_account = destination_account
        self.destination_account_id = None
        self.source_account_id = None

    def _validate_transaction_type(self, transaction_type):
        """Validate and convert transaction type to TransactionType enum.
        
        Args:
            transaction_type (TransactionType or str): Transaction type to validate.
            
        Returns:
            TransactionType: Validated TransactionType enum value.
            
        Raises:
            ValueError: If transaction_type is an invalid string.
            TypeError: If transaction_type is not a TransactionType or string.
        """
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
        """Set the transaction description.
        
        Args:
            description (str): Description text for the transaction.
        """
        self.description = description

    def setSourceAccountID(self, sourceAccountID):
        """Set the source account ID.
        
        Args:
            sourceAccountID (str or int): FireflyIII account ID for the source account.
        """
        self.source_account_id = sourceAccountID

    def setDestinationAccountID(self, destinationAccountID):
        """Set the destination account ID.
        
        Args:
            destinationAccountID (str or int): FireflyIII account ID for the destination account.
        """
        self.destination_account_id = destinationAccountID

    def setCategoryID(self, categoryID):
        """Set the category ID for the transaction.
        
        Args:
            categoryID (str, int, float, or None): Category ID. If None, defaults to 0.
        """
        if categoryID == None:
            categoryID = 0
        self.category_id = str(int(float(categoryID)))

    def getHTMLDate(self):
        """Get the transaction date formatted for HTML datetime-local input.
        
        Returns:
            str: Date formatted as 'YYYY-MM-DDTHH:MM' for HTML datetime-local input.
        """
        return self.date.strftime('%Y-%m-%dT%H:%M')
    
    def getCounterpartyAccount(self):
        """Get the counterparty account information.
        
        Returns the account that is the counterparty (not the bank account)
        for this transaction. For withdrawals/transfers, returns destination.
        For deposits, returns source.
        
        Returns:
            dict: Dictionary with 'id' and 'name' keys for the counterparty account.
        """
        if self.transaction_type in [TransactionType.TRANSFER, TransactionType.WITHDRAWAL]:
            return {"id": self.destination_account_id if self.destination_account_id is not None else "", "name": self.destination_account}
            #return self.destination_account
        elif self.transaction_type == TransactionType.DEPOSIT:
            return {"id": self.source_account_id if self.source_account_id is not None else "", "name": self.source_account}
            #return self.source_account
    
    def getBankAccount(self):
        """Get the bank account information for this transaction.
        
        Returns the bank account (not the counterparty) for this transaction.
        For deposits, returns destination. For withdrawals/transfers, returns source.
        
        Returns:
            dict: Dictionary with 'id' and 'name' keys for the bank account.
        """
        if self.transaction_type == TransactionType.DEPOSIT:
            return {"id": self.destination_account_id if self.destination_account_id is not None else "", "name": self.destination_account}
        elif self.transaction_type in [TransactionType.TRANSFER, TransactionType.WITHDRAWAL]:
            return {"id": self.source_account_id if self.source_account_id is not None else "", "name": self.source_account}

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

