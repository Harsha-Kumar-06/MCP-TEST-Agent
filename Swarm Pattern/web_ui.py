"""
Streamlit Web UI for Portfolio Swarm System
Interactive web interface for portfolio optimization

Run with: streamlit run web_ui.py
"""
import streamlit as st
import pandas as pd
import sys
from datetime import datetime, timedelta
from portfolio_swarm.models import Portfolio, Position
from portfolio_swarm.agents import (
    MarketAnalysisAgent, RiskAssessmentAgent, TaxStrategyAgent,
    ESGComplianceAgent, AlgorithmicTradingAgent
)
from portfolio_swarm.communication import CommunicationBus
from portfolio_swarm.orchestrator import SwarmOrchestrator

# Helper function for terminal logging
def log_activity(message):
    """Print activity to terminal for visibility"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)

# Page config
st.set_page_config(
    page_title="Portfolio Swarm Optimizer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
    }
    .agent-vote {
        padding: 1rem;
        margin: 0.75rem 0;
        border-radius: 8px;
        border-left: 4px solid;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .vote-approve { 
        background: #dcfce7; 
        border-left-color: #22c55e;
        color: #166534;
    }
    .vote-reject { 
        background: #fee2e2; 
        border-left-color: #ef4444;
        color: #991b1b;
    }
    .agent-vote strong {
        font-size: 1.1rem;
        display: block;
        margin-bottom: 0.5rem;
    }
    .agent-vote em {
        display: block;
        color: #374151;
        font-style: normal;
        line-height: 1.5;
    }
</style>
""", unsafe_allow_html=True)


def create_sample_portfolio() -> Portfolio:
    """Create sample portfolio"""
    from demo import create_sample_portfolio as demo_portfolio
    return demo_portfolio()


def display_portfolio_metrics(portfolio: Portfolio):
    """Display portfolio metrics in columns"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Value", f"${portfolio.total_value:,.0f}")
    with col2:
        st.metric("Portfolio Beta", f"{portfolio.portfolio_beta:.2f}")
    with col3:
        st.metric("ESG Score", f"{portfolio.average_esg_score:.1f}")
    with col4:
        st.metric("Positions", len(portfolio.positions))


def display_sector_allocation(portfolio: Portfolio):
    """Display sector allocation chart"""
    sector_data = portfolio.sector_allocation
    df = pd.DataFrame({
        'Sector': list(sector_data.keys()),
        'Allocation (%)': list(sector_data.values())
    })
    df = df.sort_values('Allocation (%)', ascending=False)
    
    st.bar_chart(df.set_index('Sector'))


def input_position_form():
    """Form to input a portfolio position"""
    with st.form("position_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            ticker = st.text_input("Ticker Symbol", "AAPL").upper()
            shares = st.number_input("Shares", min_value=1, value=1000)
            current_price = st.number_input("Current Price ($)", min_value=0.01, value=150.0, step=0.01)
            cost_basis = st.number_input("Cost Basis ($)", min_value=0.01, value=140.0, step=0.01)
        
        with col2:
            days_ago = st.number_input("Days Since Purchase", min_value=1, value=400)
            sector = st.selectbox("Sector", [
                "Technology", "Healthcare", "Financials", "Consumer Staples",
                "Energy", "Industrials", "Utilities", "Real Estate"
            ])
            esg_score = st.slider("ESG Score", 0, 100, 70)
            beta = st.number_input("Beta", min_value=0.1, max_value=3.0, value=1.0, step=0.1)
        
        submitted = st.form_submit_button("Add Position")
        
        if submitted:
            position = Position(
                ticker=ticker,
                shares=shares,
                current_price=current_price,
                cost_basis=cost_basis,
                acquisition_date=datetime.now() - timedelta(days=days_ago),
                sector=sector,
                esg_score=esg_score,
                beta=beta
            )
            return position
    return None


def display_trade_plan(trade_plan):
    """Display trade plan with formatting"""
    st.subheader("📋 Approved Trade Plan")
    
    # Trades table
    trades_data = []
    for trade in trade_plan.trades:
        trades_data.append({
            "Action": trade.action,
            "Ticker": trade.ticker,
            "Shares": f"{trade.shares:,}",
            "Price": f"${trade.estimated_price:.2f}",
            "Value": f"${trade.notional_value:,.2f}",
            "Rationale": trade.rationale[:50] + "..."
        })
    
    df = pd.DataFrame(trades_data)
    st.dataframe(df, use_container_width=True)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Tax Liability", f"${trade_plan.expected_tax_liability:,.0f}")
    with col2:
        st.metric("Execution Cost", f"${trade_plan.expected_execution_cost:,.0f}")
    with col3:
        st.metric("Total Cost", f"${trade_plan.net_cost:,.0f}")
    with col4:
        st.metric("Timeline", f"{trade_plan.execution_timeline_days} days")


def display_agent_votes(votes):
    """Display agent votes with color coding"""
    st.subheader("🗳️ Agent Votes")
    
    for vote in votes:
        vote_class = "vote-approve" if vote.vote.value == "approve" else "vote-reject"
        symbol = "✅" if vote.vote.value == "approve" else "❌"
        agent_name = vote.agent_type.value.replace('_', ' ').title()
        
        st.markdown(f"""
        <div class="agent-vote {vote_class}">
            <strong>{symbol} {agent_name}</strong>
            {vote.rationale}
        </div>
        """, unsafe_allow_html=True)


def main():
    """Main Streamlit app"""
    
    # Header
    st.markdown('<div class="main-header">🤖 Portfolio Swarm Optimizer</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Portfolio source
        portfolio_source = st.radio(
            "Portfolio Source",
            ["Sample Portfolio ($50M)", "Text Description", "Upload File", "Custom Portfolio"]
        )
        
        st.divider()
        
        # Swarm configuration
        st.subheader("Swarm Settings")
        max_iterations = st.slider("Max Iterations", 1, 20, 10)
        consensus_threshold = st.slider("Consensus Threshold", 0.5, 1.0, 0.6, 0.05)
        require_unanimous = st.checkbox("Require Unanimous Approval (100%)", False)
        
        if require_unanimous:
            st.warning("⚠️ Unanimous approval requires ALL agents to approve. This may prevent consensus if there are conflicting requirements (e.g., ESG violations).")
        elif consensus_threshold >= 0.9:
            st.info("ℹ️ High threshold may make consensus difficult to reach.")
        
        st.divider()
        
        # Agent selection
        st.subheader("Active Agents")
        use_market = st.checkbox("Market Analysis", True)
        use_risk = st.checkbox("Risk Assessment", True)
        use_tax = st.checkbox("Tax Strategy", True)
        use_esg = st.checkbox("ESG Compliance", True)
        use_trading = st.checkbox("Algorithmic Trading", True)
        
        st.divider()
        
        # Clear results button
        if st.button("🗑️ Clear All Results"):
            for key in ['result', 'orchestrator', 'portfolio', 'positions']:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("Cleared!")
    
    # Main area
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Portfolio", "🤖 Optimize", "📈 Results", "📖 Documentation"])
    
    # Tab 1: Portfolio Input/View
    with tab1:
        if portfolio_source == "Sample Portfolio ($50M)":
            if st.button("Load Sample Portfolio"):
                st.session_state.portfolio = create_sample_portfolio()
                # Clear previous results
                if 'result' in st.session_state:
                    del st.session_state.result
                if 'orchestrator' in st.session_state:
                    del st.session_state.orchestrator
                st.success("✅ Sample portfolio loaded!")
        
        elif portfolio_source == "Text Description":
            st.subheader("📝 Describe Your Portfolio")
            
            # Show sample format
            with st.expander("📖 View Sample Format"):
                st.markdown("""
                **Just describe your portfolio naturally! Here are examples:**
                
                **Example 1 - Simple:**
                ```
                I own 10,000 shares of Apple (AAPL) bought at $150, now at $185.
                Also have 5,000 Microsoft (MSFT) shares, cost basis $350, current price $410.
                Plus 3,000 Tesla shares at $245 (bought at $195).
                Cash balance: $500,000
                ```
                
                **Example 2 - Detailed:**
                ```
                Portfolio:
                - AAPL: 10,000 shares, purchased June 2023 at $150, currently $185, Tech sector, ESG 75
                - MSFT: 5,000 shares, bought Sept 2022 at $350, now $410, Technology, ESG 82
                - JNJ: 8,000 shares, cost $155, current $162, Healthcare, ESG 72
                
                Cash: $1,000,000
                Limit technology to 30%
                Minimum ESG score: 65
                ```
                
                **Example 3 - Conversational:**
                ```
                My tech portfolio has Apple (15k shares @ $185, bought for $140), 
                Microsoft (8k shares, paid $305 now worth $410), and some Tesla 
                (3k shares at $245). I have $2M in cash. Want to keep tech under 35%.
                ```
                """)
            
            # Text input area
            portfolio_text = st.text_area(
                "Paste or type your portfolio description:",
                height=200,
                placeholder="Example: I own 10,000 AAPL at $185 (bought at $150), 5,000 MSFT at $410..."
            )
            
            if st.button("🔍 Parse Portfolio") and portfolio_text:
                try:
                    log_activity("📝 Parsing portfolio text...")
                    log_activity(f"   Text length: {len(portfolio_text)} characters")
                    
                    # Save the text to debug file
                    with open('debug_ui_input.txt', 'w', encoding='utf-8') as f:
                        f.write(portfolio_text)
                    log_activity("   Saved input to debug_ui_input.txt")
                    
                    # Clear all caches to force fresh import
                    import sys
                    if 'portfolio_swarm.text_parser' in sys.modules:
                        del sys.modules['portfolio_swarm.text_parser']
                    
                    from portfolio_swarm.text_parser import parse_portfolio_text
                    portfolio = parse_portfolio_text(portfolio_text)
                    log_activity(f"✅ Successfully parsed {len(portfolio.positions)} positions")
                    if len(portfolio.positions) > 0:
                        log_activity(f"   Tickers: {[p.ticker for p in portfolio.positions]}")
                    
                    # Store and clear old results
                    st.session_state.portfolio = portfolio
                    if 'result' in st.session_state:
                        del st.session_state.result
                    if 'orchestrator' in st.session_state:
                        del st.session_state.orchestrator
                    
                    st.success(f"✅ Parsed {len(portfolio.positions)} positions!")
                    
                except Exception as e:
                    st.error(f"❌ Could not parse portfolio: {str(e)}")
                    st.info("💡 Try using the sample format above or upload a CSV/JSON file instead.")
        
        elif portfolio_source == "Custom Portfolio":
            st.subheader("Build Custom Portfolio")
            
            # Initialize positions list in session state
            if 'positions' not in st.session_state:
                st.session_state.positions = []
            
            # Add position form
            new_position = input_position_form()
            if new_position:
                st.session_state.positions.append(new_position)
                st.success(f"✅ Added {new_position.ticker}")
            
            # Show current positions
            if st.session_state.positions:
                st.subheader("Current Positions")
                positions_data = []
                for p in st.session_state.positions:
                    positions_data.append({
                        "Ticker": p.ticker,
                        "Shares": p.shares,
                        "Value": f"${p.market_value:,.2f}",
                        "Sector": p.sector
                    })
                st.dataframe(pd.DataFrame(positions_data), use_container_width=True)
                
                # Create portfolio button
                col1, col2 = st.columns(2)
                with col1:
                    cash = st.number_input("Cash Balance ($)", min_value=0.0, value=1000000.0, step=100000.0)
                with col2:
                    if st.button("Create Portfolio"):
                        st.session_state.portfolio = Portfolio(
                            positions=st.session_state.positions,
                            cash=cash,
                            policy_limits={"technology_limit": 30.0}
                        )
                        # Clear previous results
                        if 'result' in st.session_state:
                            del st.session_state.result
                        if 'orchestrator' in st.session_state:
                            del st.session_state.orchestrator
                        st.success("✅ Portfolio created!")
        
        elif portfolio_source == "Upload File":
            uploaded_file = st.file_uploader(
                "Upload portfolio file",
                type=['csv', 'json', 'yaml'],
                help="Upload CSV, JSON, or YAML file with your portfolio data"
            )
            
            if uploaded_file is not None:
                log_activity(f"📁 Loading file: {uploaded_file.name}")
                try:
                    from portfolio_swarm.input_parser import PortfolioParser
                    import tempfile
                    import os
                    
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name
                    
                    # Parse the file
                    parser = PortfolioParser()
                    portfolio = parser.parse_file(tmp_path)
                    
                    # Clean up temp file
                    os.unlink(tmp_path)
                    
                    # Store in session state and clear old results
                    st.session_state.portfolio = portfolio
                    if 'result' in st.session_state:
                        del st.session_state.result
                    if 'orchestrator' in st.session_state:
                        del st.session_state.orchestrator
                    
                    st.success(f"✅ Portfolio loaded from {uploaded_file.name}!")
                    
                    # Show validation warnings
                    warnings = parser.validate_portfolio(portfolio)
                    if warnings:
                        st.warning("⚠️ Validation warnings:")
                        for w in warnings:
                            st.text(f"  • {w}")
                    
                except Exception as e:
                    st.error(f"❌ Error loading file: {str(e)}")
        
        # Display portfolio if exists
        if 'portfolio' in st.session_state:
            st.divider()
            st.subheader("📊 Portfolio Overview")
            
            portfolio = st.session_state.portfolio
            display_portfolio_metrics(portfolio)
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Sector Allocation")
                display_sector_allocation(portfolio)
            
            with col2:
                st.subheader("Compliance Status")
                violations = portfolio.get_compliance_violations()
                if violations:
                    for v in violations:
                        st.error(f"⚠️ {v}")
                else:
                    st.success("✅ No compliance violations")
    
    # Tab 2: Optimization
    with tab2:
        if 'portfolio' not in st.session_state:
            st.warning("⚠️ Please create or load a portfolio first (Portfolio tab)")
        else:
            st.subheader("🤖 Run Swarm Optimization")
            
            portfolio = st.session_state.portfolio
            
            # Show configuration
            st.info(f"""
            **Configuration:**
            - Max Iterations: {max_iterations}
            - Consensus Threshold: {consensus_threshold:.0%}
            - Require Unanimous: {require_unanimous}
            """)
            
            if st.button("🚀 Start Optimization", type="primary"):
                with st.spinner("Running swarm optimization..."):
                    # Initialize agents
                    comm_bus = CommunicationBus()
                    agents = []
                    
                    if use_market:
                        agents.append(MarketAnalysisAgent(comm_bus))
                    if use_risk:
                        agents.append(RiskAssessmentAgent(comm_bus))
                    if use_tax:
                        agents.append(TaxStrategyAgent(comm_bus))
                    if use_esg:
                        agents.append(ESGComplianceAgent(comm_bus))
                    if use_trading:
                        agents.append(AlgorithmicTradingAgent(comm_bus))
                    
                    # Validate minimum 2 agents for meaningful multi-agent debate
                    if len(agents) < 2:
                        st.error(f"⚠️ Multi-agent debate requires at least 2 active agents ({len(agents)} selected). "
                                 "A single agent automatically results in 100% consensus, defeating the purpose of swarm intelligence.")
                        st.stop()
                    
                    # Create orchestrator
                    log_activity(f"🤖 Initializing swarm with {len(agents)} agents...")
                    orchestrator = SwarmOrchestrator(
                        agents=agents,
                        max_iterations=max_iterations,
                        consensus_threshold=consensus_threshold,
                        require_unanimous=require_unanimous
                    )
                    
                    # Run optimization
                    log_activity("🔄 Starting swarm optimization process...")
                    result = orchestrator.run_rebalancing_swarm(portfolio)
                    log_activity(f"✅ Optimization complete! Consensus: {result.approved}, Approval rate: {result.approval_rate:.1%}")
                    
                    # Store results
                    st.session_state.result = result
                    st.session_state.orchestrator = orchestrator
                
                st.success("✅ Optimization complete!")
                st.balloons()
    
    # Tab 3: Results
    with tab3:
        if 'result' not in st.session_state:
            st.info("ℹ️ Run optimization first to see results")
        else:
            result = st.session_state.result
            orchestrator = st.session_state.orchestrator
            
            # Summary
            if result.approved:
                st.success(f"🎉 Consensus Achieved! ({result.approval_rate:.0%} approval)")
            else:
                st.warning(f"⚠️ No Full Consensus ({result.approval_rate:.0%} approval)")
                st.info("The agents debated but couldn't reach the required consensus threshold. Below is the best proposal that was considered.")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Approval Rate", f"{result.approval_rate:.0%}", 
                         delta="Consensus" if result.approved else "No Consensus",
                         delta_color="normal" if result.approved else "off")
            with col2:
                st.metric("Iterations Used", f"{result.iteration + 1}/{orchestrator.max_iterations}")
            with col3:
                st.metric("Messages Exchanged", len(orchestrator.comm_bus.messages))
            
            st.divider()
            
            # Agent votes
            st.subheader("🗳️ Agent Votes")
            display_agent_votes(result.votes)
            
            st.divider()
            
            # Trade plan
            st.subheader("📋 Trade Recommendations")
            if result.trade_plan:
                if not result.approved:
                    st.caption("⚠️ Note: This plan did not achieve full consensus. Review agent concerns below before proceeding.")
                display_trade_plan(result.trade_plan)
            else:
                st.warning("No trade plan was generated. The agents could not agree on any proposal.")
            
            # Download results
            st.divider()
            if st.button("📥 Download Full Report"):
                report = orchestrator.get_debate_summary()
                st.download_button(
                    "Download Debate Transcript",
                    report,
                    file_name=f"swarm_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
    
    # Tab 4: Documentation
    with tab4:
        st.header("📖 Documentation")
        
        st.markdown("""
        ## How to Use
        
        1. **Portfolio Tab**: Create or load a portfolio
        2. **Optimize Tab**: Configure swarm settings and run optimization
        3. **Results Tab**: View consensus results and trade recommendations
        
        ## Input Requirements
        
        ### Portfolio Data
        - **Positions**: Stock ticker, shares, prices, acquisition date
        - **Cash**: Available cash balance
        - **Policy Limits**: Max sector allocations (e.g., 30% tech)
        
        ### Swarm Configuration
        - **Max Iterations**: How many debate rounds (1-20)
        - **Consensus Threshold**: Minimum approval rate (50-100%)
        - **Unanimous**: Require all agents to approve
        
        ## Output
        
        ### Trade Plan
        - List of trades (BUY/SELL with quantities)
        - Tax liability estimate
        - Execution costs and timeline
        
        ### Agent Analysis
        - Each agent's vote (APPROVE/REJECT/ABSTAIN)
        - Detailed rationale for each vote
        - Concerns and recommendations
        
        ### Debate Transcript
        - Full message history
        - Inter-agent discussions
        - Consensus formation process
        
        ## Agent Roles
        
        - **Market Analysis**: Valuation, trends, sentiment
        - **Risk Assessment**: Compliance, VaR, concentration
        - **Tax Strategy**: Capital gains optimization
        - **ESG Compliance**: Sustainability criteria
        - **Algorithmic Trading**: Execution feasibility
        
        ## Tips
        
        - Start with sample portfolio to see how it works
        - Adjust consensus threshold if no agreement reached
        - Enable/disable specific agents to test scenarios
        - Download full transcript for audit trail
        """)


if __name__ == "__main__":
    main()
