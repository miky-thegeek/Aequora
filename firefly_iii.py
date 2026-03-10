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
import os

from oauthlib.oauth2 import WebApplicationClient
import requests
import urllib
import base64
import logging
import secrets

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FireflyIII:

    def __init__(self, baseURL, clientID, clientSecret):
        """Initialize FireflyIII client.
        
        Args:
            baseURL (str): Base URL of the FireflyIII instance.
            clientID (str): OAuth2 client ID.
            clientSecret (str): OAuth2 client secret.
            
        Raises:
            ValueError: If any required parameter is missing.
        """
        self.base_url = baseURL.rstrip('/') + '/'  # Ensure trailing slash
        self.client_id = clientID
        self.client_secret = clientSecret
        self.client = WebApplicationClient(self.client_id)
        
        # Validate required parameters
        if not self.base_url or not self.client_id or not self.client_secret:
            raise ValueError("Missing required parameters: baseURL, clientID, or clientSecret")

    def startAuth(self):
        """Start OAuth2 authentication flow.
        
        Generates authorization URL with state parameter for CSRF protection.
        
        Returns:
            str: Authorization URL to redirect user to.
            
        Raises:
            Exception: If authorization URL generation fails.
        """
        try:

            # Generate state parameter for CSRF protection
            state = secrets.token_urlsafe(32)
            self.state = state

            APP_HOST = os.getenv('APP_HOST', '0.0.0.0')
            APP_PORT = int(os.getenv('APP_PORT', 8443))

            redirect_uri = f'https://{APP_HOST}:{APP_PORT}/oauth2_callback'
            print(f"Generated redirect URI: {redirect_uri}")
            logger.info(f"Generated redirect URI: {redirect_uri}")

            return self.client.prepare_request_uri(
                self.base_url+"oauth/authorize",
                redirect_uri = redirect_uri,
                state = state
            )
        except Exception as e:
            logger.error(f"Error in startAuth: {e}")
            raise
    
    def continueAuth(self, code, state=None):
        """Continue OAuth2 authentication flow with authorization code.
        
        Exchanges authorization code for access token and refresh token.
        
        Args:
            code (str): Authorization code from OAuth2 callback.
            state (str, optional): State parameter for CSRF protection.
                                 Defaults to None.
        
        Returns:
            bool: True if authentication successful, False otherwise.
        """
        if not code:
            logger.error("No authorization code provided")
            return False

        if state and hasattr(self, 'state') and state != self.state:
            logger.error("State parameter mismatch - possible CSRF attack")
            return False

        try:
            APP_HOST = os.getenv('APP_HOST', '0.0.0.0')
            APP_PORT = int(os.getenv('APP_PORT', 8443))

            data = self.client.prepare_request_body(
                code = code,
                redirect_uri = f'https://{APP_HOST}:{APP_PORT}/oauth2_callback',
                client_id = self.client_id,
                client_secret = self.client_secret
            )
            token_url = self.base_url+"oauth/token"
            
            client_id = urllib.parse.quote(self.client_id.encode('utf8'))
            clientSecret = urllib.parse.quote(self.client_secret.encode('utf8'))
            code_bytes = f"{client_id}:{clientSecret}".encode('ascii')
            base64_bytes = base64.b64encode(code_bytes)
            base64_code = base64_bytes.decode('ascii')

            headers ={ 'Content-Type': "application/x-www-form-urlencoded", 'Authorization': f"Basic {base64_code}"}

            response = requests.post(token_url, data=data, headers=headers, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Token request failed with status {response.status_code}: {response.text}")
                return False
                
            response_data = response.json()
            if response_data.get('hint') == "Authorization code has expired":
                logger.warning("Authorization code has expired")
                return False
            
            if hasattr(self, 'state'):
                delattr(self, 'state')
            
            #print("response: "+str(response.json()))
            self.client.parse_request_body_response(response.text)
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error in continueAuth: {e}")
            return False
        except Exception as e:
            logger.error(f"Error in continueAuth: {e}")
            return False

    
    def checkAccessToken(self):
        """Check if access token is valid and refresh if expired.
        
        Verifies access token exists and is not expired. If expired,
        attempts to refresh using refresh token.
        
        Returns:
            bool: True if valid access token exists, False otherwise.
        """
        print("token: "+str(self.client.token))
        #print("checkAccessToken: "+str(self.client.token))
        try:
            if hasattr(self.client, 'token') and self.client.token and 'access_token' in self.client.token:
                #print(f"client.token: {self.client.token}")
                # Check if token is expired
                if 'expires_at' in self.client.token:
                    import time
                    if time.time() > self.client.token['expires_at']:
                        logger.info("Access token expired, attempting refresh")
                        return self._refreshToken()
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Error checking access token: {e}")
            return False

    def _refreshToken(self):
        """Refresh the access token using refresh token.
        
        Uses the refresh token to obtain a new access token from
        the OAuth2 token endpoint.
        
        Returns:
            bool: True if token refresh successful, False otherwise.
        """
        try:
            if not hasattr(self.client, 'token') or not self.client.token or 'refresh_token' not in self.client.token:
                logger.error("No refresh token available")
                return False
                
            token_url = self.base_url+"oauth/token"
            
            client_id = urllib.parse.quote(self.client_id.encode('utf8'))
            clientSecret = urllib.parse.quote(self.client_secret.encode('utf8'))
            code_bytes = f"{client_id}:{clientSecret}".encode('ascii')
            base64_bytes = base64.b64encode(code_bytes)
            base64_code = base64_bytes.decode('ascii')

            headers = {
                'Content-Type': "application/x-www-form-urlencoded", 
                'Authorization': f"Basic {base64_code}"
            }
            
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.client.token['refresh_token']
            }

            response = requests.post(token_url, data=data, headers=headers, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Token refresh failed with status {response.status_code}: {response.text}")
                return False
                
            response_data = response.json()
            
            if 'error' in response_data:
                logger.error(f"OAuth2 refresh error: {response_data.get('error')}")
                return False
            
            # Update the token
            self.client.parse_request_body_response(response.text)
            return True
            
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return False

    def searchTransations(self, query, accessToken = ""):
        """Search for transactions in FireflyIII.
        
        Searches FireflyIII transactions using a query string.
        
        Args:
            query (str): Search query string (e.g., "account_id:1 amount:100.00").
            accessToken (str, optional): Access token to use. If not provided,
                                       uses token from client. Defaults to "".
        
        Returns:
            dict: FireflyIII API response with 'data' key containing transactions,
                 or {"data": []} on error.
        """
        if not query:
            logger.warning("Empty query provided to searchTransations")
            return {"data": []}
            
        try:
            if accessToken != "":
                access_token = accessToken
            else:
                if not hasattr(self.client, 'token') or not self.client.token or 'access_token' not in self.client.token:
                    logger.error("No valid access token available")
                    return {"data": []}
                access_token = self.client.token['access_token']
                
            headers = {
                'Accept': 'application/vnd.api+json',
                'Authorization': 'Bearer '+access_token 
            }
            
            # Safe URL construction
            search_url = urllib.parse.urljoin(self.base_url, "api/v1/search/transactions")
            params = {'query': query}
            
            response = requests.get(search_url, headers=headers, params=params, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Search request failed with status {response.status_code}: {response.text}")
                return {"data": []}
                
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error in searchTransations: {e}")
            return {"data": []}
        except Exception as e:
            logger.error(f"Error in searchTransations: {e}")
            return {"data": []}
    
    def autocompleteAccounts(self, query, type):
        """Autocomplete accounts in FireflyIII.
        
        Searches for accounts matching the query string and account type.
        
        Args:
            query (str): Account name or identifier to search for.
            type (str): Account type filter (e.g., "Revenue account", "Expense account").
        
        Returns:
            list or dict: FireflyIII API response with account suggestions,
                        or empty list on error.
        """
        if not query or not type:
            logger.warning("Empty query or type provided to autocompleteAccounts")
            return []
            
        try:
            if not hasattr(self.client, 'token') or not self.client.token or 'access_token' not in self.client.token:
                logger.error("No valid access token available")
                return []
                
            headers = {
                'Accept': 'application/vnd.api+json',
                'Authorization': 'Bearer '+self.client.token['access_token'] 
            }
            
            # Safe URL construction
            autocomplete_url = urllib.parse.urljoin(self.base_url, "api/v1/autocomplete/accounts")
            params = {
                'query': query,
                'types': f"Asset account,{type}"
            }
            
            try:
                response = requests.get(autocomplete_url, headers=headers, params=params, timeout=30)
            except TypeError:
                logger.warning("TypeError in autocompleteAccounts, trying with empty query")
                params['query'] = ""
                response = requests.get(autocomplete_url, headers=headers, params=params, timeout=30)

            if response.status_code != 200:
                logger.error(f"Autocomplete request failed with status {response.status_code}: {response.text}")
                return []

            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error in autocompleteAccounts: {e}")
            return []
        except Exception as e:
            logger.error(f"Error in autocompleteAccounts: {e}")
            return []
    
    def getCategories(self):
        """Get all categories from FireflyIII.
        
        Retrieves all categories from the FireflyIII instance.
        
        Returns:
            dict: FireflyIII API response with 'data' key containing categories,
                 or {"data": []} on error.
        """
        try:
            if not hasattr(self.client, 'token') or not self.client.token or 'access_token' not in self.client.token:
                logger.error("No valid access token available")
                return {"data": []}
                
            headers = {
                'Accept': 'application/vnd.api+json',
                'Authorization': 'Bearer '+self.client.token['access_token'] 
            }
            
            # Safe URL construction
            categories_url = urllib.parse.urljoin(self.base_url, "api/v1/categories")
            params = {'limit': 500}
            
            response = requests.get(categories_url, headers=headers, params=params, timeout=30)

            if response.status_code != 200:
                logger.error(f"Categories request failed with status {response.status_code}: {response.text}")
                return {"data": []}

            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error in getCategories: {e}")
            return {"data": []}
        except Exception as e:
            logger.error(f"Error in getCategories: {e}")
            return {"data": []}
    
    def getTransactionsOfAccount(self, accountID):
        """Get all transactions for a specific account.
        
        Retrieves transaction history for a given account ID.
        
        Args:
            accountID (str or int): FireflyIII account ID.
        
        Returns:
            dict: FireflyIII API response with 'data' key containing transactions,
                 or {"data": []} on error.
        """
        if not accountID:
            #logger.warning("Empty accountID provided to getTransactionsOfAccount")
            return {"data": []}
            
        try:
            if not hasattr(self.client, 'token') or not self.client.token or 'access_token' not in self.client.token:
                logger.error("No valid access token available")
                return {"data": []}
                
            headers = {
                'Accept': 'application/vnd.api+json',
                'Authorization': 'Bearer '+self.client.token['access_token'] 
            }
            
            # Safe URL construction
            transactions_url = urllib.parse.urljoin(self.base_url, f"api/v1/accounts/{accountID}/transactions")
            
            response = requests.get(transactions_url, headers=headers, timeout=30)

            if response.status_code != 200:
                logger.error(f"Transactions request failed with status {response.status_code}: {response.text}")
                return {"data": []}

            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error in getTransactionsOfAccount: {e}")
            return {"data": []}
        except Exception as e:
            logger.error(f"Error in getTransactionsOfAccount: {e}")
            return {"data": []}
    
    def insertTransactions(self, dictonaryData):
        """Insert transactions into FireflyIII.
        
        Creates new transactions in FireflyIII using the provided data.
        
        Args:
            dictonaryData (dict): Transaction data dictionary following
                                FireflyIII API format with 'transactions' key.
        
        Returns:
            dict: FireflyIII API response with created transactions, or
                 {"error": "..."} on error.
        """
        if not dictonaryData:
            logger.warning("Empty data provided to insertTransactions")
            return {"error": "No data provided"}
            
        try:
            if not hasattr(self.client, 'token') or not self.client.token or 'access_token' not in self.client.token:
                logger.error("No valid access token available")
                return {"error": "No valid access token"}
                
            headers = {
                'Accept': 'application/vnd.api+json',
                'Authorization': 'Bearer '+self.client.token['access_token'] 
            }
            
            # Safe URL construction
            transactions_url = urllib.parse.urljoin(self.base_url, "api/v1/transactions")
            
            response = requests.post(transactions_url, json=dictonaryData, headers=headers, timeout=30)

            if response.status_code not in [200, 201]:
                logger.error(f"Insert transactions request failed with status {response.status_code}: {response.text}")
                return {"error": f"Request failed with status {response.status_code}"}

            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error in insertTransactions: {e}")
            return {"error": f"Network error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error in insertTransactions: {e}")
            return {"error": f"Unexpected error: {str(e)}"}