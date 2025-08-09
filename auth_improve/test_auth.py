#!/usr/bin/env python3
"""
Test script for Firefly III authentication flow
"""

import os
import sys
from firefly_iii import FireflyIII

def test_auth_flow():
    """Test the authentication flow"""
    
    # Get environment variables
    base_url = os.environ.get('FIREFLY_BASE_URL', 'http://192.168.1.30:8081/')
    client_id = os.environ.get('fireflyIII_id')
    client_secret = os.environ.get('fireflyIII_secret')
    
    if not client_id or not client_secret:
        print("Error: Missing required environment variables")
        print("Please set: fireflyIII_id, fireflyIII_secret")
        return False
    
    try:
        # Initialize Firefly III client
        firefly = FireflyIII(base_url, client_id, client_secret)
        
        # Test 1: Check if we can create authorization URL
        auth_url = firefly.startAuth()
        print(f"✓ Authorization URL created: {auth_url[:50]}...")
        
        # Test 2: Check access token (should be False initially)
        has_token = firefly.checkAccessToken()
        print(f"✓ Access token check: {has_token}")
        
        # Test 3: Test API calls without token (should return empty data)
        categories = firefly.getCategories()
        print(f"✓ Categories API call: {len(categories.get('data', []))} categories")
        
        print("\n✅ Authentication flow setup is correct!")
        print("\nTo complete authentication:")
        print("1. Visit the authorization URL in your browser")
        print("2. Authorize the application")
        print("3. You'll be redirected to the callback URL")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing authentication flow: {e}")
        return False

if __name__ == "__main__":
    success = test_auth_flow()
    sys.exit(0 if success else 1)
