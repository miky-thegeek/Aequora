from enum import Enum

class AccountType(Enum):
    CHECKING_ACCOUNT = "checking_account"
    DEBIT_CARD = "debit_card"
    PREPAID_CARD = "prepaid_card"
    PAYPAL = "paypal"

class Account:

    def __init__(self, id):
        """Initialize an Account object.
        
        Args:
            id (str): Account identifier (e.g., 'checkingAccount_1', 'paypal_1').
        """
        self.id = id
        self.account_type = self._calculate_account_type(id)
        
    
    def _calculate_account_type(self, id):
        """Calculate account type from account ID.
        
        Parses the account ID to determine the account type based on the prefix.
        
        Args:
            id (str): Account identifier with prefix indicating type.
            
        Returns:
            AccountType: AccountType enum value corresponding to the account prefix.
        """
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
        """Set the associated account ID.
        
        Used for debit cards to link them to their associated checking account.
        
        Args:
            idAssociatedAccount (str): ID of the associated account.
        """
        self.id_associated_account = idAssociatedAccount
    
    def setBank(self, bank):
        """Set the bank name for this account.
        
        Args:
            bank (str): Bank name (e.g., 'Unicredit', 'PostePay').
        """
        self.bank = bank
    
    def setDataframe(self, dataframe):
        """Set the pandas DataFrame containing account transaction data.
        
        Args:
            dataframe (pandas.DataFrame): DataFrame containing transaction data
                                         for this account.
        """
        self.dataframe = dataframe

