"""Test the loan underwriter system"""
import requests
import json

# Test application - Jennifer Martinez (ideal approval candidate)
application = {
    "applicant": {
        "first_name": "Jennifer",
        "last_name": "Martinez",
        "email": "jennifer.martinez@email.com",
        "phone": "415-555-0142",
        "ssn": "XXX-XX-7821",
        "date_of_birth": "1988-03-15",
        "annual_income": 185000,
        "employment_status": "employed",
        "employer_name": "Pacific Northwest Medical Center",
        "job_title": "Senior Clinical Pharmacist",
        "years_employed": 8
    },
    "property": {
        "address": "2847 Hillcrest Drive",
        "city": "Portland",
        "state": "OR",
        "zip_code": "97205",
        "property_type": "single_family",
        "purchase_price": 625000,
        "estimated_value": 635000
    },
    "loan": {
        "loan_amount": 475000,
        "loan_type": "conventional",
        "loan_term": 30,
        "interest_rate_type": "fixed",
        "down_payment": 150000
    }
}

print("=" * 60)
print("LOAN UNDERWRITER - FULL SYSTEM TEST")
print("=" * 60)
print(f"\nApplicant: {application['applicant']['first_name']} {application['applicant']['last_name']}")
print(f"Income: ${application['applicant']['annual_income']:,}")
print(f"Property: {application['property']['address']}, {application['property']['city']}, {application['property']['state']}")
print(f"Loan Amount: ${application['loan']['loan_amount']:,}")
print(f"Down Payment: ${application['loan']['down_payment']:,} ({application['loan']['down_payment']/application['property']['purchase_price']*100:.1f}%)")

print("\nSubmitting application...")
print("-" * 60)

try:
    response = requests.post(
        "http://127.0.0.1:8000/api/applications",
        json=application,
        timeout=120
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ APPLICATION PROCESSED SUCCESSFULLY!")
        print(f"\nApplication ID: {result.get('application_id', 'N/A')}")
        print(f"Decision: {result.get('decision', 'N/A').upper()}")
        print(f"Overall Score: {result.get('overall_score', 'N/A')}")
        
        # Agent results
        if 'agent_results' in result:
            print("\n" + "=" * 60)
            print("AGENT ANALYSIS RESULTS")
            print("=" * 60)
            
            for agent_name, agent_data in result['agent_results'].items():
                print(f"\n📊 {agent_name.upper().replace('_', ' ')}")
                print("-" * 40)
                if isinstance(agent_data, dict):
                    risk_score = agent_data.get('risk_score', agent_data.get('score'))
                    risk_level = agent_data.get('risk_level', agent_data.get('level'))
                    if risk_score:
                        print(f"   Risk Score: {risk_score}")
                    if risk_level:
                        print(f"   Risk Level: {risk_level}")
                    
                    # Show findings/flags
                    findings = agent_data.get('findings', agent_data.get('flags', []))
                    if findings:
                        print(f"   Findings:")
                        for f in findings[:5]:
                            print(f"      - {f}")
        
        # Recommendations
        if result.get('recommendations'):
            print("\n" + "=" * 60)
            print("RECOMMENDATIONS")
            print("=" * 60)
            for rec in result['recommendations'][:5]:
                print(f"   • {rec}")
                
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text[:500])
        
except requests.exceptions.ConnectionError:
    print("\n❌ Could not connect to server. Make sure it's running on http://127.0.0.1:8000")
except Exception as e:
    print(f"\n❌ Error: {e}")
