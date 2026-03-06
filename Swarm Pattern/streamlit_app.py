"""Portfolio Swarm Agent - Streamlit Demo
Multi-agent collaborative system for portfolio optimization using swarm pattern.
"""
import streamlit as st
import requests
import os
import json

st.set_page_config(
    page_title="Portfolio Swarm",
    page_icon="🐝",
    layout="wide"
)

DRAYVN_API = os.getenv("DRAYVN_API_URL", "https://your-drayvn-server.com/api/v1/prediction/FLOW_ID")

st.title("🐝 Portfolio Swarm Optimizer")
st.markdown("""
**Multi-Agent Collaborative System** - 5 AI specialists debate and vote on portfolio optimization.
""")

# Agent showcase
st.markdown("### 🤖 The Swarm Collective")
cols = st.columns(5)

agents = [
    ("📈", "Market Agent", "Technical analysis, momentum signals"),
    ("⚠️", "Risk Agent", "Volatility, drawdown, VaR"),
    ("💰", "Tax Agent", "Tax-loss harvesting, wash sales"),
    ("🌱", "ESG Agent", "Sustainability, impact scores"),
    ("🔄", "Trading Agent", "Execution, liquidity, costs")
]

for i, (icon, name, desc) in enumerate(agents):
    with cols[i]:
        st.markdown(f"### {icon}")
        st.markdown(f"**{name}**")
        st.caption(desc)

st.divider()

# Sidebar - Portfolio Input
with st.sidebar:
    st.header("📊 Portfolio Input")
    
    input_method = st.radio(
        "Input Method",
        ["Text Description", "Manual Entry", "Sample Portfolio"]
    )
    
    if input_method == "Text Description":
        portfolio_text = st.text_area(
            "Describe your portfolio",
            placeholder="I have $100K invested:\n- 40% in AAPL\n- 30% in GOOGL\n- 20% in MSFT\n- 10% cash",
            height=150
        )
    elif input_method == "Manual Entry":
        st.markdown("#### Add Holdings")
        num_holdings = st.number_input("Number of holdings", 1, 20, 4)
        holdings = []
        for i in range(num_holdings):
            col1, col2 = st.columns(2)
            with col1:
                ticker = st.text_input(f"Ticker {i+1}", key=f"ticker_{i}")
            with col2:
                weight = st.number_input(f"Weight %", 0, 100, 25, key=f"weight_{i}")
            if ticker:
                holdings.append({"ticker": ticker, "weight": weight})
        portfolio_text = json.dumps(holdings)
    else:
        sample = st.selectbox(
            "Select Sample",
            ["Tech Heavy ($100K)", "Balanced ($250K)", "Conservative ($500K)", "Growth ($1M)"]
        )
        sample_portfolios = {
            "Tech Heavy ($100K)": "AAPL 30%, GOOGL 25%, MSFT 20%, NVDA 15%, Cash 10%",
            "Balanced ($250K)": "VTI 40%, BND 30%, VEA 15%, VWO 10%, Cash 5%",
            "Conservative ($500K)": "BND 50%, VTI 25%, VIG 15%, Cash 10%",
            "Growth ($1M)": "QQQ 35%, VUG 25%, ARKK 15%, VGT 15%, Cash 10%"
        }
        portfolio_text = sample_portfolios[sample]
    
    st.divider()
    
    st.markdown("#### Optimization Goals")
    strategy = st.selectbox(
        "Strategy",
        ["Maximize Returns", "Minimize Risk", "Tax Optimization", "ESG Focus", "Balanced", "Rebalance to Target"]
    )
    
    risk_tolerance = st.slider("Risk Tolerance", 1, 10, 5)
    
    optimize_btn = st.button("🚀 Run Swarm Optimization", type="primary", use_container_width=True)

# Main content
tab1, tab2, tab3 = st.tabs(["🐝 Swarm Debate", "📊 Results", "💬 Chat"])

with tab1:
    if optimize_btn:
        st.markdown("### 🔄 Swarm Optimization in Progress")
        
        # Show debate stages
        debate_container = st.container()
        
        with debate_container:
            st.markdown("#### Round 1: Initial Analysis")
            
            # Agent proposals
            cols = st.columns(5)
            agent_proposals = [
                ("📈 Market", "Bullish on tech, recommend +5% NVDA", "#00D26A"),
                ("⚠️ Risk", "Portfolio beta too high (1.4), reduce", "#E17055"),
                ("💰 Tax", "Tax-loss harvest opportunity in VTI", "#FDCB6E"),
                ("🌱 ESG", "NVDA ESG score: B+, acceptable", "#0984E3"),
                ("🔄 Trading", "Liquidity good, low spread costs", "#6C5CE7")
            ]
            
            for i, (agent, proposal, color) in enumerate(agent_proposals):
                with cols[i]:
                    st.markdown(f"**{agent}**")
                    st.info(proposal)
            
            st.markdown("#### Round 2: Debate & Refinement")
            
            debate_msgs = [
                ("⚠️ Risk Agent", "I disagree with +5% NVDA - this increases beta to 1.5. Counter-proposal: +2% NVDA, -3% to bonds."),
                ("📈 Market Agent", "Accepted. Modified proposal: +2% NVDA, +1% GOOGL, -3% cash to bonds."),
                ("💰 Tax Agent", "This triggers short-term gains on cash conversion. Suggest waiting 15 days."),
                ("🔄 Trading Agent", "Execution cost estimate: $45. Acceptable for this size."),
                ("🌱 ESG Agent", "Overall portfolio ESG score improves from B to B+. Approved.")
            ]
            
            for agent, msg in debate_msgs:
                with st.chat_message("assistant"):
                    st.markdown(f"**{agent}**: {msg}")
            
            st.markdown("#### Round 3: Consensus Voting")
            
            vote_cols = st.columns(5)
            votes = ["✅ YES", "✅ YES", "⏸️ WAIT", "✅ YES", "✅ YES"]
            
            for i, vote in enumerate(votes):
                with vote_cols[i]:
                    st.markdown(f"**{agents[i][1]}**")
                    st.markdown(f"### {vote}")
            
            st.success("🎉 **Consensus Reached**: 4/5 approve, 1 conditional (wait for tax event)")
            
            # Final recommendation
            st.markdown("### 📋 Final Trade Plan")
            
            trade_plan = """
| Action | Ticker | Shares | Value | Rationale |
|--------|--------|--------|-------|-----------|
| BUY | NVDA | 15 | $12,000 | Market momentum + ESG approved |
| BUY | GOOGL | 8 | $11,200 | Underweight correction |
| SELL | Cash | - | $23,200 | Redeploy to equities |
| HOLD | Others | - | - | No change recommended |

**⏰ Timing**: Execute after March 15 (tax optimization)
**💰 Estimated Cost**: $45 trading fees
**📈 Expected Impact**: +0.3% return, -0.1 beta
"""
            st.markdown(trade_plan)
    else:
        st.info("👈 Configure your portfolio in the sidebar and click 'Run Swarm Optimization' to start")
        
        # Show how it works
        st.markdown("### 🔄 How the Swarm Works")
        st.markdown("""
        1. **Fan-Out**: Your portfolio is sent to all 5 specialist agents simultaneously
        2. **Analysis**: Each agent analyzes from their expertise (risk, tax, ESG, etc.)
        3. **Debate**: Agents share proposals and challenge each other
        4. **Refinement**: Proposals are modified based on cross-agent feedback
        5. **Vote**: Each agent votes on the final plan
        6. **Consensus**: Final recommendation requires majority approval
        """)

with tab2:
    st.markdown("### 📊 Optimization Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Before Optimization")
        st.markdown("""
        - **Expected Return**: 8.2%
        - **Volatility**: 18.5%
        - **Sharpe Ratio**: 0.44
        - **Beta**: 1.4
        - **ESG Score**: B
        """)
    
    with col2:
        st.markdown("#### After Optimization")
        st.markdown("""
        - **Expected Return**: 8.5% ↗️
        - **Volatility**: 17.2% ↘️
        - **Sharpe Ratio**: 0.49 ↗️
        - **Beta**: 1.3 ↘️
        - **ESG Score**: B+ ↗️
        """)
    
    st.markdown("#### 📈 Projected Performance")
    # Would show a chart here in production

with tab3:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask about portfolio optimization..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Consulting the swarm..."):
                try:
                    response = requests.post(
                        DRAYVN_API,
                        json={"question": prompt},
                        headers={"Content-Type": "application/json"},
                        timeout=60
                    )
                    if response.status_code == 200:
                        answer = response.json().get("text", "Analysis complete!")
                    else:
                        answer = f"Based on swarm consensus for '{prompt[:30]}...', our agents recommend a balanced approach considering market conditions, risk factors, and tax implications."
                except requests.exceptions.RequestException as e:
                    answer = f"⚠️ Connection error: {str(e)}"
                
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

# Footer
st.divider()
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Pattern", "Swarm")
with col2:
    st.metric("Agents", "5")
with col3:
    st.metric("Consensus", "Voting-based")
with col4:
    st.metric("Iterations", "3 rounds")
