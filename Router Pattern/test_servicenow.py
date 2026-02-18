import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth

# Load environment variables
load_dotenv()

# Get credentials
instance_url = os.getenv("SERVICENOW_INSTANCE", "").rstrip("/")
username = os.getenv("SERVICENOW_USERNAME")
password = os.getenv("SERVICENOW_PASSWORD")

print("=== Environment Check ===")
print(f"Instance: {instance_url}")
print(f"Username: {username}")
print(f"Password: {'*' * len(password) if password else 'NOT SET'}")

if not all([instance_url, username, password]):
    print("\n❌ Missing environment variables!")
    exit(1)

api_url = f"{instance_url}/api/now"

print("\n=== Testing Connection ===")
try:
    response = requests.get(
        f"{api_url}/table/incident?sysparm_limit=1",
        auth=HTTPBasicAuth(username, password),
        headers={"Accept": "application/json"},
        timeout=30
    )
    
    if response.status_code == 200:
        print("✅ Connection successful!")
        
        print("\n=== Creating Test Ticket ===")
        create_response = requests.post(
            f"{api_url}/table/incident",
            auth=HTTPBasicAuth(username, password),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            json={
                "short_description": "Test Ticket from Python API",
                "description": "Automated test ticket from CorpAssist integration.",
                "urgency": "2",
                "impact": "2"
            },
            timeout=30
        )
        
        if create_response.status_code in [200, 201]:
            result = create_response.json().get("result", {})
            print(f"✅ Ticket created!")
            print(f"   🎫 Number: {result.get('number')}")
            print(f"   🔑 Sys ID: {result.get('sys_id')}")
            print(f"\n🔗 View: {instance_url}/incident.do?sys_id={result.get('sys_id')}")
        else:
            print(f"❌ Create failed: {create_response.status_code}")
            print(create_response.text)
    
    elif response.status_code == 401:
        print("❌ Authentication failed! Check credentials")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)

except requests.exceptions.Timeout:
    print("❌ Timeout - Wake up instance first:")
    print(f"   👉 {instance_url}")
except Exception as e:
    print(f"❌ Error: {e}")
