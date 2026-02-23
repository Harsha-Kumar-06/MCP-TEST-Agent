"""Test Experian API with GDP proxy endpoint"""
import requests
import os
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv('EXPERIAN_CLIENT_ID')
client_secret = os.getenv('EXPERIAN_CLIENT_SECRET')
username = os.getenv('EXPERIAN_USERNAME')
password = os.getenv('EXPERIAN_PASSWORD')

# Get token using Basic Auth for client credentials
print("Getting OAuth token...")
r = requests.post(
    'https://sandbox-us-api.experian.com/oauth2/v1/token', 
    data={
        'username': username,
        'password': password,
        'grant_type': 'password'
    },
    auth=(client_id, client_secret)
)

if r.status_code != 200:
    print(f"Token error: {r.status_code} - {r.text}")
    exit(1)

token = r.json()['access_token']
print(f"Token obtained: {token[:50]}...")

# Use GDP proxy like original curl
target_url = "https://sandbox-us-api.experian.com/consumerservices/credit-profile/v1/connect-check"
encoded_target = urllib.parse.quote(target_url, safe='')
api_url = f"https://sandbox-us-api.experian.com/eits/gdp/v1/request?targeturl={encoded_target}"

body = {
    "consumerPii": {
        "primaryApplicant": {
            "name": {
                "lastName": "CONSUMER",
                "firstName": "JONATHAN"
            },
            "ssn": {
                "ssn": "666-60-3472"
            },
            "currentAddress": {
                "line1": "10655 N BIRCH ST",
                "city": "BURBANK",
                "state": "CA",
                "zipCode": "91502"
            }
        }
    },
    "requestor": {
        "subscriberCode": "2222222"
    },
    "permissiblePurpose": {
        "type": "3F"
    }
}

# Also test with double quotes in JSON
import json
print("\nRequest body:")
print(json.dumps(body, indent=2))

print(f"\nCalling connect-check API directly...")
print(f"URL: {api_url}")

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'clientReferenceId': 'SBMYSQL'
}

# Use data instead of json parameter to match curl behavior
r2 = requests.post(api_url, data=json.dumps(body), headers=headers)

print(f'Status: {r2.status_code}')

if r2.status_code == 200:
    data = r2.json()
    print('\n✅ SUCCESS!')
    import json
    print(json.dumps(data, indent=2)[:2000])
else:
    print(f'\n❌ Error: {r2.text[:500]}')
