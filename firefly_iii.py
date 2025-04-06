from oauthlib.oauth2 import WebApplicationClient
import requests
import urllib
import base64

class FireflyIII:

    def __init__(self, baseURL, clientID, clientSecret):
        self.base_url = baseURL
        self.client_id = clientID
        self.client_secret = clientSecret
        self.client = WebApplicationClient(self.client_id)

    def startAuth(self):
        return self.client.prepare_request_uri(
            self.base_url+"oauth/authorize",
            redirect_uri = 'https://192.168.1.25:8443/oauth2_callback',
        )
    
    def continueAuth(self, code):
        data = self.client.prepare_request_body(
            code = code,
            redirect_uri = 'https://192.168.1.25:8443/oauth2_callback',
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

        response = requests.post(token_url, data=data, headers=headers)
        if response.json().get('hint') == "Authorization code has expired":
            return False
        
        #print("response: "+str(response.json()))
        self.client.parse_request_body_response(response.text)
        return True

    
    def checkAccessToken(self):
        #print("token: "+str(self.client.token))
        if 'access_token' in self.client.token:
            return True
        else:
            return False
        
    def searchTransations(self, query):
        headers = {
            'Accept': 'application/vnd.api+json',
            'Authorization': 'Bearer '+self.client.token['access_token'] }
        response = requests.request("GET", self.base_url+"api/v1/search/transactions?query="+urllib.parse.quote(query), headers=headers)

        return response.json()
    
    def autocompleteAccounts(self, query, type):
        headers = {
            'Accept': 'application/vnd.api+json',
            'Authorization': 'Bearer '+self.client.token['access_token'] }
        response = requests.request("GET", self.base_url+"api/v1/autocomplete/accounts?query="+urllib.parse.quote(query)+"&types="+urllib.parse.quote("Asset account,"+type), headers=headers)

        return response.json()
    
    def getCategories(self):
        headers = {
            'Accept': 'application/vnd.api+json',
            'Authorization': 'Bearer '+self.client.token['access_token'] }
        response = requests.request("GET", self.base_url+"api/v1/categories?limit=500", headers=headers)

        return response.json()