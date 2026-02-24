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

# Use GDP proxy endpoint with targeturl
target_url = "https://sandbox-us-api.experian.com/consumerservices/credit-profile/v1/connect-check"
encoded_target = urllib.parse.quote(target_url, safe='')
gdp_url = f"https://sandbox-us-api.experian.com/eits/gdp/v1/request?targeturl={encoded_target}"

body = {
    'consumerPii': {
        'primaryApplicant': {
            'name': {
                'lastName': 'CONSUMER',
                'firstName': 'JONATHAN',
                'middleName': '',
                'generationCode': ''
            },
            'ssn': {
                'ssn': '666603472'
            },
            'currentAddress': {
                'line1': '10655 N BIRCH ST',
                'city': 'BURBANK',
                'state': 'CA',
                'zipCode': '91502'
            }
        }
    },
    'requestor': {
        'subscriberCode': '2222222'
    },
    'permissiblePurpose': {
        'type': '3F'
    },
    'addOns': {
        'riskModels': {
            'modelIndicator': ['V4'],
            'scorePercentile': 'Y'
        }
    }
}

print(f"\nCalling GDP proxy endpoint...")
print(f"Target: {target_url}")

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'clientReferenceId': 'SBMYSQL'
}

r2 = requests.post(gdp_url, json=body, headers=headers)

print(f'Status: {r2.status_code}')

if r2.status_code == 200:
    data = r2.json()
    print('\n✅ SUCCESS!')
    import json
    print(json.dumps(data, indent=2)[:1000])
else:
    print(f'\n❌ Error: {r2.text[:500]}')

if r.status_code != 200:
    print(f"Token error: {r.status_code} - {r.text}")
    exit(1)

token = r.json()['access_token']
print(f"Token obtained: {token[:30]}...")

# Try minimal format - no empty strings
body = {
    'consumerPii': {
        'primaryApplicant': {
            'name': {
                'lastName': 'CONSUMER',
                'firstName': 'JONATHAN'
            },
            'ssn': {
                'ssn': '666603472'
            },
            'currentAddress': {
                'line1': '10655 N BIRCH ST',
                'city': 'BURBANK',
                'state': 'CA',
                'zipCode': '91502'
            }
        }
    },
    'requestor': {
        'subscriberCode': '2222222'
    },
    'permissiblePurpose': {
        'type': '3F'
    }
}

print("\nTrying different header cases...")
import json

test_headers = [
    {'companyId': 'SBMYSQL'},
    {'companyid': 'SBMYSQL'},
    {'COMPANYID': 'SBMYSQL'},
    {'Company-Id': 'SBMYSQL'},
    {'company_id': 'SBMYSQL'},
]

for extra_header in test_headers:
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        **extra_header
    }
    header_name = list(extra_header.keys())[0]
    r2 = requests.post(
        'https://sandbox-us-api.experian.com/consumerservices/credit-profile/v2/credit-report',
        json=body,
        headers=headers
    )
    print(f"{header_name}: {r2.status_code} - {r2.text[:80]}...")

print(f'Status: {r2.status_code}')

if r2.status_code == 200:
    data = r2.json()
    cp = data.get('creditProfile', {})
    print('\n✅ SUCCESS! Got credit profile')
    if cp.get('riskModel'):
        print(f"Credit Score: {cp['riskModel'][0].get('score', 'N/A')}")
    print(f"Tradelines: {len(cp.get('tradeline', []))}")
else:
    print(f'\n❌ Error: {r2.text[:500]}')
