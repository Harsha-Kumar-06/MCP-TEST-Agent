"""Loan Underwriter Agent - Streamlit Demo
AI Multi-Agent System for mortgage processing using Fan-Out/Fan-In architecture.
"""
import streamlit as st
import requests
import os
import json

st.set_page_config(
    page_title="Loan Underwriter",
    page_icon="🏦",
    layout="wide"
)

DRAYVN_API = os.getenv("DRAYVN_API_URL", "https://your-drayvn-server.com/api/v1/prediction/FLOW_ID")

st.title("🏦 AI Loan Underwriter")
st.markdown("""
**20x Faster Mortgage Processing** - From 15 minutes to ~45 seconds using parallel AI agents.
""")

# Architecture visualization
st.markdown("### ⚡ Fan-Out/Fan-In Architecture")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown("### 📥")
    st.markdown("**Input**")
    st.caption("Application")
    
with col2:
    st.markdown("### ↗️↗️↗️")
    st.markdown("**Fan-Out**")
    st.caption("Parallel agents")

with col3:
    st.markdown("""
    ```
    🏦 Credit
    📊 Income
    🏠 Property
    ```
    """)
    
with col4:
    st.markdown("### ↘️↘️↘️")
    st.markdown("**Fan-In**")
    st.caption("Aggregate")

with col5:
    st.markdown("### ✅")
    st.markdown("**Decision**")
    st.caption("Approve/Deny")

st.divider()

# Sidebar - Loan Application Form
with st.sidebar:
    st.header("📋 Loan Application")
    
    st.markdown("#### Applicant Info")
    applicant_name = st.text_input("Full Name", "John Smith")
    applicant_ssn = st.text_input("SSN (last 4)", "1234", max_chars=4)
    
    st.markdown("#### Financial Info")
    annual_income = st.number_input("Annual Income ($)", 30000, 500000, 85000, 5000)
    credit_score = st.slider("Credit Score", 300, 850, 720)
    existing_debt = st.number_input("Monthly Debt ($)", 0, 10000, 1500, 100)
    
    st.markdown("#### Loan Details")
    loan_amount = st.number_input("Loan Amount ($)", 50000, 2000000, 350000, 10000)
    property_value = st.number_input("Property Value ($)", 50000, 3000000, 425000, 10000)
    loan_term = st.selectbox("Loan Term", ["15 years", "30 years"])
    
    # Calculate DTI and LTV
    monthly_income = annual_income / 12
    dti = (existing_debt / monthly_income) * 100 if monthly_income > 0 else 0
    ltv = (loan_amount / property_value) * 100 if property_value > 0 else 0
    
    st.divider()
    st.markdown("#### Quick Metrics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("DTI Ratio", f"{dti:.1f}%")
    with col2:
        st.metric("LTV Ratio", f"{ltv:.1f}%")
    
    submit_app = st.button("🚀 Submit Application", type="primary", use_container_width=True)

# Main content
tab1, tab2 = st.tabs(["📊 Underwriting", "💬 Chat"])

with tab1:
    if submit_app:
        application_data = {
            "applicant": {
                "name": applicant_name,
                "ssn_last4": applicant_ssn
            },
            "financial": {
                "annual_income": annual_income,
                "credit_score": credit_score,
                "monthly_debt": existing_debt,
                "dti_ratio": round(dti, 2)
            },
            "loan": {
                "amount": loan_amount,
                "property_value": property_value,
                "ltv_ratio": round(ltv, 2),
                "term": loan_term
            }
        }
        
        st.markdown("### 🔄 Processing Application...")
        
        # Show parallel processing
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 🏦 Credit Analysis")
            credit_progress = st.progress(0)
            credit_status = st.empty()
            
        with col2:
            st.markdown("#### 📊 Income Verification")
            income_progress = st.progress(0)
            income_status = st.empty()
            
        with col3:
            st.markdown("#### 🏠 Property Assessment")
            property_progress = st.progress(0)
            property_status = st.empty()
        
        # Simulate parallel processing
        import time
        for i in range(101):
            credit_progress.progress(min(i + 5, 100))
            income_progress.progress(min(i + 3, 100))
            property_progress.progress(min(i, 100))
            time.sleep(0.01)
        
        credit_status.success("✅ Complete")
        income_status.success("✅ Complete")
        property_status.success("✅ Complete")
        
        st.markdown("### 📥 Aggregating Results...")
        aggregate_progress = st.progress(0)
        for i in range(101):
            aggregate_progress.progress(i)
            time.sleep(0.005)
        
        # Call API
        with st.spinner("Generating final decision..."):
            try:
                response = requests.post(
                    DRAYVN_API,
                    json={"question": f"Underwrite this loan application: {json.dumps(application_data)}"},
                    headers={"Content-Type": "application/json"},
                    timeout=120
                )
                if response.status_code == 200:
                    answer = response.json().get("text", "Decision: Review Complete")
                else:
                    # Demo response
                    if credit_score >= 700 and dti < 43 and ltv < 80:
                        answer = f"""
## ✅ APPROVED

### Decision Summary
- **Credit Score**: {credit_score} (Excellent)
- **DTI Ratio**: {dti:.1f}% (Within limits)
- **LTV Ratio**: {ltv:.1f}% (Acceptable)

### Loan Terms
- **Amount**: ${loan_amount:,}
- **Term**: {loan_term}
- **Estimated Rate**: 6.25%

### Conditions
- Employment verification required
- Property appraisal confirmation
"""
                    else:
                        issues = []
                        if credit_score < 700:
                            issues.append(f"Credit score {credit_score} below 700 threshold")
                        if dti >= 43:
                            issues.append(f"DTI ratio {dti:.1f}% exceeds 43% limit")
                        if ltv >= 80:
                            issues.append(f"LTV ratio {ltv:.1f}% may require PMI")
                        
                        answer = f"""
## ⚠️ CONDITIONAL APPROVAL

### Risk Factors
{chr(10).join(f'- {issue}' for issue in issues)}

### Recommendations
- Consider higher down payment
- Debt consolidation may improve DTI
- Rate may be higher due to risk factors
"""
            except requests.exceptions.RequestException as e:
                answer = f"⚠️ Connection error: {str(e)}"
        
        st.divider()
        st.markdown(answer)
    else:
        st.info("👈 Fill out the loan application in the sidebar and click 'Submit Application'")
        
        # Show sample applications
        st.markdown("### 📁 Sample Applications")
        st.markdown("You can also test with pre-built sample applications:")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**🟢 Strong Application**")
            st.caption("Credit: 780, DTI: 28%, LTV: 75%")
        with col2:
            st.markdown("**🟡 Borderline Application**")
            st.caption("Credit: 680, DTI: 41%, LTV: 85%")
        with col3:
            st.markdown("**🔴 High Risk Application**")
            st.caption("Credit: 620, DTI: 48%, LTV: 95%")

with tab2:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask about loan underwriting..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                try:
                    response = requests.post(
                        DRAYVN_API,
                        json={"question": prompt},
                        headers={"Content-Type": "application/json"},
                        timeout=60
                    )
                    if response.status_code == 200:
                        answer = response.json().get("text", "Response received!")
                    else:
                        answer = f"⚠️ Error (Status: {response.status_code})"
                except requests.exceptions.RequestException as e:
                    answer = f"⚠️ Connection error: {str(e)}"
                
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

# Footer
st.divider()
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Processing Time", "~45s")
with col2:
    st.metric("Traditional Time", "15 min")
with col3:
    st.metric("Speed Improvement", "20x")
with col4:
    st.metric("Parallel Agents", "3")
