from enum import Enum

class AccountType(Enum):
    CHECKING_ACCOUNT = "checking_account"
    DEBIT_CARD = "debit_card"
    PREPAID_CARD = "prepaid_card"
    PAYPAL = "paypal"

class Account:

    def __init__(self, id, dataframe):
        self.id = id
        self.dataframe = dataframe
        self.account_type = self._calculate_account_type(id)
        
    
    def _calculate_account_type(self, id):
        accountTypeHTML = id.split('_')[0]
        accountType = ""

        if accountTypeHTML == "checkingAccount":
            accountType = AccountType.CHECKING_ACCOUNT
        elif accountTypeHTML == "debitCard":
            accountType = AccountType.DEBIT_CARD
        elif accountTypeHTML == "prepaidCard":
            accountType = AccountType.PREPAID_CARD
        elif accountTypeHTML == "paypal":
            accountType = AccountType.PAYPAL
        
        return accountType
    
    def setAssociation(self, idAssociatedAccount):
        self.id_associated_account = idAssociatedAccount