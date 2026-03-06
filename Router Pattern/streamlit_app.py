"""HelpDesk Bot (Router Pattern) - Streamlit Demo
AI-powered internal support agent that routes requests to specialized agents.
"""
import streamlit as st
import requests
import os

st.set_page_config(
    page_title="HelpDesk Bot",
    page_icon="🤖",
    layout="wide"
)

DRAYVN_API = os.getenv("DRAYVN_API_URL", "https://your-drayvn-server.com/api/v1/prediction/FLOW_ID")

st.title("🤖 HelpDesk Bot")
st.markdown("""
**AI-Powered Internal Support** using the Router Pattern to classify and route requests to expert agents.
""")

# Architecture visualization
st.markdown("### 🎯 Router Architecture")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown("### 👥")
    st.markdown("**HR Agent**")
    st.caption("PTO, Benefits, Payroll, Policies")

with col2:
    st.markdown("### 💻")
    st.markdown("**IT Support**")
    st.caption("Hardware, Software, Access, Passwords")

with col3:
    st.markdown("### 💰")
    st.markdown("**Sales Agent**")
    st.caption("Quotes, Pricing, CRM, Customers")

with col4:
    st.markdown("### ⚖️")
    st.markdown("**Legal Agent**")
    st.caption("Contracts, Compliance, NDAs")

with col5:
    st.markdown("### 🚫")
    st.markdown("**Off-Topic**")
    st.caption("Politely redirect")

st.divider()

# Sidebar
with st.sidebar:
    st.header("🎯 Quick Requests")
    
    st.markdown("#### HR Questions")
    if st.button("📅 Check PTO Balance"):
        st.session_state.quick_prompt = "What is my current PTO balance and how do I request time off?"
    if st.button("💰 Benefits Info"):
        st.session_state.quick_prompt = "Can you explain the company health insurance options?"
    
    st.markdown("#### IT Support")
    if st.button("🔑 Password Reset"):
        st.session_state.quick_prompt = "I need to reset my password for the company VPN"
    if st.button("💻 Laptop Issue"):
        st.session_state.quick_prompt = "My laptop is running very slow and freezes often"
    
    st.markdown("#### Sales")
    if st.button("📊 CRM Access"):
        st.session_state.quick_prompt = "I need access to Salesforce CRM for a new project"
    
    st.markdown("#### Legal")
    if st.button("📝 NDA Request"):
        st.session_state.quick_prompt = "I need an NDA template for a new vendor relationship"
    
    st.divider()
    st.info("💡 The router automatically detects your intent and routes to the appropriate specialist agent")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Handle quick prompts
if "quick_prompt" in st.session_state:
    prompt = st.session_state.quick_prompt
    del st.session_state.quick_prompt
    st.session_state.messages.append({"role": "user", "content": prompt})

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Process any pending user message
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_msg = st.session_state.messages[-1]["content"]
    
    # Check if we already have a response for this message
    if len(st.session_state.messages) < 2 or st.session_state.messages[-2]["role"] != "assistant":
        with st.chat_message("assistant"):
            # Determine routing
            routing_text = st.empty()
            
            # Simple keyword-based routing for demo
            msg_lower = last_msg.lower()
            if any(word in msg_lower for word in ["pto", "vacation", "benefits", "payroll", "hr"]):
                route = "👥 HR Agent"
                color = "#00D26A"
            elif any(word in msg_lower for word in ["password", "laptop", "software", "vpn", "access", "it"]):
                route = "💻 IT Support"
                color = "#0984E3"
            elif any(word in msg_lower for word in ["quote", "pricing", "crm", "salesforce", "customer", "sales"]):
                route = "💰 Sales Agent"
                color = "#FDCB6E"
            elif any(word in msg_lower for word in ["nda", "contract", "legal", "compliance"]):
                route = "⚖️ Legal Agent"
                color = "#E17055"
            else:
                route = "🤖 General Assistant"
                color = "#6C5CE7"
            
            routing_text.markdown(f"**Routing to: {route}**")
            
            with st.spinner(f"Processing with {route}..."):
                try:
                    response = requests.post(
                        DRAYVN_API,
                        json={"question": last_msg},
                        headers={"Content-Type": "application/json"},
                        timeout=60
                    )
                    if response.status_code == 200:
                        answer = response.json().get("text", "Request processed!")
                    else:
                        # Demo response based on routing
                        if "HR" in route:
                            answer = f"""
**HR Agent Response** 👥

Based on your request about "{last_msg[:50]}...":

📅 **PTO Information:**
- Current balance: 15 days remaining
- Accrual rate: 1.25 days/month
- Request process: Submit via HR portal → Manager approval → Confirmation email

📋 **Next Steps:**
1. Log into HR Portal (hr.company.com)
2. Navigate to Time Off → Request New
3. Select dates and submit

Need anything else HR-related?
"""
                        elif "IT" in route:
                            answer = f"""
**IT Support Response** 💻

Regarding your issue: "{last_msg[:50]}..."

🔧 **Troubleshooting Steps:**
1. Restart your device
2. Clear browser cache
3. Check network connection

🎫 **Ticket Created:** IT-2024-{hash(last_msg) % 10000:04d}
- Priority: Medium
- Assigned to: IT Support Team
- Expected response: Within 4 hours

💡 **Quick Fix:** Try restarting while holding Shift key for a clean boot.
"""
                        elif "Sales" in route:
                            answer = f"""
**Sales Agent Response** 💰

For your request: "{last_msg[:50]}..."

📊 **CRM Access:**
- Access level: Standard User
- Training: Available at sales-training.company.com
- Support: sales-ops@company.com

📈 **Quick Resources:**
- Quote templates: /Shared/Sales/Templates
- Pricing guide: Updated Q1 2024
- Customer lookup: CRM Dashboard → Search

Need a walkthrough? I can schedule a 15-min demo.
"""
                        elif "Legal" in route:
                            answer = f"""
**Legal Agent Response** ⚖️

Regarding: "{last_msg[:50]}..."

📝 **Document Templates:**
- Standard NDA: [Download from Legal Portal]
- Vendor Agreement: [Requires Legal Review]
- Contract Amendment: [Submit via Legal Request]

⚠️ **Important:**
- All contracts require Legal team review before signing
- Turnaround time: 3-5 business days
- Rush requests: Email legal@company.com with "URGENT"

Shall I initiate a legal review request?
"""
                        else:
                            answer = f"""
I understand you're asking about: "{last_msg[:50]}..."

This doesn't seem to fall under our standard support categories (HR, IT, Sales, Legal). 

Here's what I can help with:
- 👥 **HR**: PTO, benefits, payroll, policies
- 💻 **IT**: Hardware, software, access issues
- 💰 **Sales**: CRM, quotes, pricing
- ⚖️ **Legal**: Contracts, NDAs, compliance

Could you rephrase your request or let me know which department might help?
"""
                except requests.exceptions.RequestException as e:
                    answer = f"⚠️ Connection error: {str(e)}"
                
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

# Chat input
if prompt := st.chat_input("How can I help you today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# Footer
st.divider()
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Pattern", "Router")
with col2:
    st.metric("Specialist Agents", "5")
with col3:
    st.metric("Categories", "HR, IT, Sales, Legal")
with col4:
    st.metric("Response Time", "<3s")
