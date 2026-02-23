"""
Test script to verify API keys and check which services return real data.
"""

import os
import asyncio
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_google_api_key():
    """Test Google AI (Gemini) API key."""
    print("\n" + "="*60)
    print("TESTING: Google AI (Gemini) API Key")
    print("="*60)
    
    api_key = os.getenv("GOOGLE_API_KEY", "")
    
    if not api_key or api_key == "your_google_api_key_here":
        print("❌ GOOGLE_API_KEY not set or is placeholder")
        return False
    
    print(f"   Key found: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        from google import genai
        
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="Say 'API key is valid' in exactly 4 words"
        )
        
        result_text = response.text.strip()
        print(f"✅ GOOGLE API KEY WORKING!")
        print(f"   Response: {result_text[:100]}")
        return True
        
    except Exception as e:
        print(f"❌ Google API Error: {str(e)}")
        return False


def test_rentcast_api():
    """Test RentCast API key."""
    print("\n" + "="*60)
    print("TESTING: RentCast API Key (Property Valuation)")
    print("="*60)
    
    api_key = os.getenv("RENTCAST_API_KEY", "")
    
    if not api_key or api_key == "mock_key":
        print("❌ RENTCAST_API_KEY not set or is mock_key")
        return False
    
    print(f"   Key found: {api_key[:8]}...{api_key[-4:]}")
    
    # Test with a sample address
    try:
        url = "https://api.rentcast.io/v1/properties"
        
        params = {
            "address": "5500 Grand Lake Dr, San Antonio, TX 78244"
        }
        
        headers = {
            "X-Api-Key": api_key,
            "Accept": "application/json"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ RENTCAST API WORKING!")
            print(f"   Response status: {response.status_code}")
            if data:
                print(f"   Sample data keys: {list(data.keys()) if isinstance(data, dict) else 'array response'}")
            return True
        elif response.status_code == 401:
            print(f"❌ API returned 401 - Key may be invalid")
            print(f"   Response: {response.text[:200]}")
            return False
        elif response.status_code == 429:
            print(f"⚠️  API returned 429 - Rate limited (key may still be valid)")
            return "rate_limited"
        else:
            print(f"❌ API Error: Status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ RentCast API Error: {str(e)}")
        return False


def test_attom_api():
    """Test ATTOM API key."""
    print("\n" + "="*60)
    print("TESTING: ATTOM API Key (Property Data)")
    print("="*60)
    
    api_key = os.getenv("ATTOM_API_KEY", "")
    
    if not api_key or api_key == "mock_key":
        print("❌ ATTOM_API_KEY not set or is mock_key")
        print("   Using: SIMULATED DATA")
        return False
    
    print(f"   Key found: {api_key[:8]}...")
    
    try:
        # ATTOM API test endpoint
        url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/detail"
        
        params = {
            "address1": "123 Main Street",
            "address2": "San Antonio, TX 78244"
        }
        
        headers = {
            "apikey": api_key,
            "Accept": "application/json"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ ATTOM API WORKING!")
            return True
        else:
            print(f"❌ ATTOM API Error: Status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ ATTOM API Error: {str(e)}")
        return False


def test_experian_api():
    """Test Experian API credentials."""
    print("\n" + "="*60)
    print("TESTING: Experian API (Credit/Financial Data)")
    print("="*60)
    
    client_id = os.getenv("EXPERIAN_CLIENT_ID", "")
    client_secret = os.getenv("EXPERIAN_CLIENT_SECRET", "")
    username = os.getenv("EXPERIAN_USERNAME", "")
    password = os.getenv("EXPERIAN_PASSWORD", "")
    env = os.getenv("EXPERIAN_ENV", "sandbox")
    
    if not client_id or client_id == "your_experian_client_id_here":
        print("❌ EXPERIAN_CLIENT_ID not set or is placeholder")
        print("   Using: SIMULATED DATA")
        return False
    
    if not client_secret or client_secret == "your_experian_client_secret_here":
        print("❌ EXPERIAN_CLIENT_SECRET not set or is placeholder")
        print("   Using: SIMULATED DATA")
        return False
    
    if not username or username == "your_experian_username_here":
        print("❌ EXPERIAN_USERNAME not set or is placeholder")
        print("   Using: SIMULATED DATA")
        return False
    
    if not password or password == "your_experian_password_here":
        print("❌ EXPERIAN_PASSWORD not set or is placeholder")
        print("   Using: SIMULATED DATA")
        return False
    
    print(f"   Client ID found: {client_id[:8]}...")
    print(f"   Username found: {username[:4]}...")
    print(f"   Environment: {env}")
    
    try:
        # Test Experian OAuth token endpoint
        base_url = "https://sandbox-us-api.experian.com" if env == "sandbox" else "https://us-api.experian.com"
        
        response = requests.post(
            f"{base_url}/oauth2/v1/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "username": username,
                "password": password,
                "grant_type": "password"
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            },
            timeout=15
        )
        
        if response.status_code == 200:
            print(f"   ✓ OAuth token obtained successfully")
            print(f"✅ EXPERIAN API WORKING!")
            print(f"   Note: Credit Report API requires 'Consumer Credit Profile' product")
            print(f"   Enable at: https://developer.experian.com")
            return True
        elif response.status_code == 401:
            print(f"❌ Experian API Error: Invalid credentials")
            print(f"   Response: {response.text[:200]}")
            return False
        else:
            print(f"❌ Experian API Error: Status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Experian API Error: {str(e)}")
        return False


def test_persona_api():
    """Test Persona API key."""
    print("\n" + "="*60)
    print("TESTING: Persona API (Identity Verification)")
    print("="*60)
    
    api_key = os.getenv("PERSONA_API_KEY", "")
    
    if not api_key or api_key == "your_persona_api_key_here":
        print("❌ PERSONA_API_KEY not set or is placeholder")
        print("   Using: SIMULATED DATA")
        return False
    
    print(f"   Key found: {api_key[:8]}...")
    
    try:
        # Test Persona API
        response = requests.get(
            "https://withpersona.com/api/v1/inquiries",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Persona-Version": "2023-01-05"
            },
            params={"page[size]": 1},
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ PERSONA API WORKING!")
            return True
        else:
            print(f"❌ Persona API Error: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Persona API Error: {str(e)}")
        return False


def print_summary(results):
    """Print a summary of all API test results."""
    print("\n" + "="*60)
    print("SUMMARY: API Key Status")
    print("="*60)
    
    status_icons = {
        True: "✅ REAL DATA",
        False: "❌ SIMULATED",
        "rate_limited": "⚠️  RATE LIMITED"
    }
    
    for service, status in results.items():
        icon = status_icons.get(status, status_icons[False])
        print(f"   {service:25} {icon}")
    
    print("\n" + "-"*60)
    
    working = sum(1 for v in results.values() if v is True)
    simulated = sum(1 for v in results.values() if v is False)
    
    print(f"   Working APIs:   {working}/{len(results)}")
    print(f"   Simulated APIs: {simulated}/{len(results)}")
    
    if working > 0:
        print(f"\n   ✅ The system is using REAL DATA from {working} service(s)")
    if simulated > 0:
        print(f"   ⚠️  {simulated} service(s) are using SIMULATED/MOCK data")


def main():
    """Run all API tests."""
    print("\n" + "#"*60)
    print("#     LOAN UNDERWRITER - API KEY VERIFICATION TEST")
    print("#"*60)
    
    results = {}
    
    # Test each API
    results["Google AI (Gemini)"] = test_google_api_key()
    results["RentCast (Property)"] = test_rentcast_api()
    results["ATTOM (Property)"] = test_attom_api()
    results["Experian (Credit)"] = test_experian_api()
    results["Persona (Fraud)"] = test_persona_api()
    
    # Print summary
    print_summary(results)
    
    return results


if __name__ == "__main__":
    main()
