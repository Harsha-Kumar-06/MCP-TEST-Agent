"""Check ServiceNow tickets from terminal"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# ServiceNow credentials
INSTANCE = os.getenv("SERVICENOW_INSTANCE", "https://dev229808.service-now.com")
USERNAME = os.getenv("SERVICENOW_USERNAME", "admin")
PASSWORD = os.getenv("SERVICENOW_PASSWORD")

def list_recent_incidents():
    """List recent incidents from ServiceNow"""
    url = f"{INSTANCE}/api/now/table/incident"
    params = {
        "sysparm_limit": 15,
        "sysparm_order_by": "sys_created_on",
        "sysparm_order": "desc",
        "sysparm_display_value": "true",
        "sysparm_fields": "number,short_description,state,priority,assignment_group,sys_created_on,caller_id,category"
    }
    
    try:
        response = requests.get(
            url,
            auth=(USERNAME, PASSWORD),
            headers={"Accept": "application/json"},
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            incidents = response.json().get("result", [])
            print(f"\n{'='*70}")
            print(f"  SERVICENOW INCIDENTS - Found {len(incidents)} recent tickets")
            print(f"{'='*70}\n")
            
            if not incidents:
                print("  No incidents found in ServiceNow.")
                return []
            
            for i, inc in enumerate(incidents, 1):
                number = inc.get('number', 'N/A')
                desc = inc.get('short_description', 'N/A')[:50]
                state = inc.get('state', 'N/A')
                priority = inc.get('priority', 'N/A')
                group = inc.get('assignment_group', 'Unassigned') or 'Unassigned'
                created = inc.get('sys_created_on', 'N/A')
                
                print(f"  {i}. [{number}] {desc}")
                print(f"     State: {state} | Priority: {priority}")
                print(f"     Assignment Group: {group}")
                print(f"     Created: {created}")
                print(f"     {'-'*60}")
            
            return incidents
        elif response.status_code == 401:
            print("  ERROR: Authentication failed. Check username/password.")
        else:
            print(f"  ERROR: {response.status_code}")
            print(f"  {response.text[:200]}")
        return []
        
    except requests.exceptions.ConnectionError:
        print("  ERROR: Cannot connect to ServiceNow. Check your internet connection.")
        return []
    except Exception as e:
        print(f"  ERROR: {e}")
        return []

def check_assignment_groups():
    """List available assignment groups in ServiceNow"""
    url = f"{INSTANCE}/api/now/table/sys_user_group"
    params = {
        "sysparm_limit": 20,
        "sysparm_fields": "name,description",
        "sysparm_query": "active=true"
    }
    
    try:
        response = requests.get(
            url,
            auth=(USERNAME, PASSWORD),
            headers={"Accept": "application/json"},
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            groups = response.json().get("result", [])
            print(f"\n{'='*70}")
            print(f"  AVAILABLE ASSIGNMENT GROUPS")
            print(f"{'='*70}\n")
            
            for g in groups:
                name = g.get('name', 'N/A')
                desc = g.get('description', '')[:40] if g.get('description') else ''
                print(f"  - {name}")
                if desc:
                    print(f"    ({desc})")
            return groups
        return []
    except Exception as e:
        print(f"  ERROR: {e}")
        return []

if __name__ == "__main__":
    print("\n" + "="*70)
    print("  SERVICENOW CONNECTION TEST")
    print("="*70)
    print(f"  Instance: {INSTANCE}")
    print(f"  Username: {USERNAME}")
    print("="*70)
    
    # List existing tickets
    list_recent_incidents()
    
    # Show available groups
    check_assignment_groups()
    
    print(f"\n{'='*70}")
    print("  HOW TO CHECK IN SERVICENOW WEB UI:")
    print("="*70)
    print(f"  1. Go to: {INSTANCE}")
    print(f"  2. Login with: {USERNAME}")
    print("  3. In left sidebar, type: incident")
    print("  4. Click: Incident > All")
    print("  5. Sort by 'Created' column (newest first)")
    print("  6. Filter by Assignment Group to see specific team tickets")
    print("="*70 + "\n")
