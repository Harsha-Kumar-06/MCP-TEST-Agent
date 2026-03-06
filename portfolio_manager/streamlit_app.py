"""Portfolio Manager Agent - Streamlit Demo
AI-powered investment portfolio creation for young investors.
"""
import streamlit as st
import requests
import os

st.set_page_config(
    page_title="Portfolio Manager",
    page_icon="📈",
    layout="wide"
)

DRAYVN_API = os.getenv("DRAYVN_API_URL", "https://your-drayvn-server.com/api/v1/prediction/FLOW_ID")

st.title("📈 Automated Portfolio Manager")
st.markdown("""
**AI Investment Agent** that creates personalized, data-driven portfolios:
- ✅ Interactive risk assessment
- ✅ Macroeconomic analysis
- ✅ Sector identification
- ✅ Stock selection & allocation
- ✅ Portfolio backtesting
""")

# Sidebar - Quick Profile Setup
with st.sidebar:
    st.header("📊 Quick Profile")
    
    age = st.slider("Your Age", 18, 65, 28)
    
    risk_tolerance = st.select_slider(
        "Risk Tolerance",
        options=["Very Conservative", "Conservative", "Moderate", "Aggressive", "Very Aggressive"],
        value="Moderate"
    )
    
    investment_amount = st.number_input(
        "Investment Amount ($)",
        min_value=1000,
        max_value=1000000,
        value=10000,
        step=1000
    )
    
    investment_horizon = st.selectbox(
        "Investment Horizon",
        ["1-2 years", "3-5 years", "5-10 years", "10+ years"]
    )
    
    goals = st.multiselect(
        "Investment Goals",
        ["Retirement", "Home Purchase", "Education", "Wealth Building", "Emergency Fund"],
        default=["Wealth Building"]
    )
    
    if st.button("🚀 Generate Portfolio", type="primary"):
        profile_summary = f"""
        Create a personalized investment portfolio:
        - Age: {age}
        - Risk Tolerance: {risk_tolerance}
        - Investment Amount: ${investment_amount:,}
        - Time Horizon: {investment_horizon}
        - Goals: {', '.join(goals)}
        """
        st.session_state.auto_prompt = profile_summary

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Handle auto-prompt from sidebar
if "auto_prompt" in st.session_state:
    prompt = st.session_state.auto_prompt
    del st.session_state.auto_prompt
    
    st.session_state.messages.append({"role": "user", "content": prompt})

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Process pending messages
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_msg = st.session_state.messages[-1]["content"]
    
    with st.chat_message("assistant"):
        with st.spinner("🤖 Running 8-agent pipeline..."):
            # Show pipeline stages
            stages = [
                "👨‍💼 Assessing user profile...",
                "🌎 Analyzing macroeconomic conditions...",
                "🏢 Identifying optimal sectors...",
                "📈 Selecting high-quality stocks...",
                "⚖️ Constructing portfolio allocation...",
                "📊 Calculating performance metrics...",
                "⏪ Running historical backtest...",
                "📝 Generating investment report..."
            ]
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, stage in enumerate(stages):
                status_text.markdown(f"**{stage}**")
                progress_bar.progress((i + 1) / len(stages))
                
            try:
                response = requests.post(
                    DRAYVN_API,
                    json={"question": last_msg},
                    headers={"Content-Type": "application/json"},
                    timeout=120
                )
                if response.status_code == 200:
                    answer = response.json().get("text", "Portfolio generated!")
                else:
                    answer = f"⚠️ Error generating portfolio (Status: {response.status_code})"
            except requests.exceptions.RequestException as e:
                answer = f"⚠️ Connection error: {str(e)}"
            
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()

# Chat input
if prompt := st.chat_input("Ask about investments or describe your goals..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# Footer
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Agents in Pipeline", "8")
with col2:
    st.metric("Data Sources", "Alpha Vantage + FRED")
with col3:
    st.metric("Analysis Type", "Fundamental + Technical")
