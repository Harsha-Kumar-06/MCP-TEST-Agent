"""
Enhanced Streamlit Web UI for Portfolio Swarm System
Features:
- Strategy selection after portfolio parsing
- Real-time progress visualization
- Agent flow visualization
- Results export (JSON, CSV, Text)
- Conversation memory
- Query templates

Run with: streamlit run enhanced_web_ui.py
"""
import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import io

# Portfolio Swarm imports
from portfolio_swarm.models import Portfolio, Position
from portfolio_swarm.agents import (
    MarketAnalysisAgent, RiskAssessmentAgent, TaxStrategyAgent,
    ESGComplianceAgent, AlgorithmicTradingAgent
)
from portfolio_swarm.communication import CommunicationBus
from portfolio_swarm.orchestrator import SwarmOrchestrator
from portfolio_swarm.strategies import (
    OptimizationStrategy, StrategyType, get_strategy, 
    create_custom_strategy, list_available_strategies, STRATEGY_TEMPLATES
)
from portfolio_swarm.logger import get_logger, SwarmLogger
from portfolio_swarm.memory import ConversationMemory, QUERY_TEMPLATES


# Page config
st.set_page_config(
    page_title="Portfolio Swarm Optimizer Pro",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced UI
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
    .strategy-card {
        background: #f8fafc;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #3b82f6;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    .strategy-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }
    .strategy-card.selected {
        border-left-color: #22c55e;
        background: #dcfce7;
    }
    .priority-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
        margin: 0.2rem;
    }
    .priority-high { background: #fef3c7; color: #92400e; }
    .priority-medium { background: #e0f2fe; color: #075985; }
    .priority-low { background: #f3f4f6; color: #374151; }
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
    .progress-step {
        display: flex;
        align-items: center;
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-radius: 6px;
    }
    .progress-step.active { background: #dbeafe; }
    .progress-step.complete { background: #dcfce7; }
    .metric-card {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
    }
    .export-btn {
        margin: 0.25rem;
    }
    .star-rating {
        color: #fbbf24;
        font-size: 1.2rem;
        letter-spacing: 2px;
    }
    .star-empty {
        color: #d1d5db;
    }
    .rating-card {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .rating-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    .rating-label {
        font-weight: 600;
        color: #374151;
    }
    .rating-description {
        color: #6b7280;
        font-size: 0.9rem;
    }
    .trade-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .trade-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .trade-action-buy {
        background: #dcfce7;
        color: #166534;
        padding: 0.25rem 0.75rem;
        border-radius: 4px;
        font-weight: 600;
    }
    .trade-action-sell {
        background: #fee2e2;
        color: #991b1b;
        padding: 0.25rem 0.75rem;
        border-radius: 4px;
        font-weight: 600;
    }
    .confidence-bar {
        height: 8px;
        background: #e5e7eb;
        border-radius: 4px;
        overflow: hidden;
        margin-top: 0.5rem;
    }
    .confidence-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.3s ease;
    }
    .confidence-high { background: linear-gradient(90deg, #22c55e, #16a34a); }
    .confidence-medium { background: linear-gradient(90deg, #fbbf24, #f59e0b); }
    .confidence-low { background: linear-gradient(90deg, #ef4444, #dc2626); }
    .overall-score {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        border-radius: 16px;
        color: white;
        margin: 1rem 0;
    }
    .overall-score .stars {
        font-size: 2.5rem;
        margin: 1rem 0;
    }
    .overall-score .score-text {
        font-size: 1.5rem;
        font-weight: bold;
    }
    .overall-score .score-description {
        opacity: 0.9;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


# Star Rating Helper Functions
def get_stars(score: float, max_score: float = 5.0) -> str:
    """Convert a score to star rating (1-5 stars)"""
    normalized = min(5, max(0, (score / max_score) * 5))
    full_stars = int(normalized)
    half_star = 1 if (normalized - full_stars) >= 0.5 else 0
    empty_stars = 5 - full_stars - half_star
    
    stars = "★" * full_stars
    if half_star:
        stars += "⯪"  # Half star
    stars += "☆" * empty_stars
    return stars


def get_stars_html(score: float, max_score: float = 5.0) -> str:
    """Get HTML formatted stars"""
    normalized = min(5, max(0, (score / max_score) * 5))
    full_stars = int(normalized)
    empty_stars = 5 - full_stars
    
    html = f'<span class="star-rating">{"★" * full_stars}</span>'
    html += f'<span class="star-rating star-empty">{"☆" * empty_stars}</span>'
    return html


def calculate_trade_score(trade, strategy) -> dict:
    """Calculate a multi-factor score for a trade recommendation"""
    scores = {
        'value_score': 0,
        'risk_score': 0,
        'alignment_score': 0,
        'overall': 0
    }
    
    # Value score based on trade size (larger = more impactful)
    if trade.notional_value > 100000:
        scores['value_score'] = 5
    elif trade.notional_value > 50000:
        scores['value_score'] = 4
    elif trade.notional_value > 20000:
        scores['value_score'] = 3
    else:
        scores['value_score'] = 2
    
    # Risk score (simplified - could be enhanced with more data)
    scores['risk_score'] = 4  # Default medium-high
    
    # Strategy alignment (check if rationale mentions strategy priorities)
    if strategy:
        priorities = strategy.priorities
        rationale_lower = trade.rationale.lower()
        alignment_hits = 0
        for priority in priorities.keys():
            if priority in rationale_lower:
                alignment_hits += 1
        scores['alignment_score'] = min(5, 2 + alignment_hits)
    else:
        scores['alignment_score'] = 3
    
    # Overall score (weighted average)
    scores['overall'] = (scores['value_score'] * 0.3 + 
                        scores['risk_score'] * 0.3 + 
                        scores['alignment_score'] * 0.4)
    
    return scores


def get_result_quality_score(result, strategy) -> dict:
    """Calculate overall result quality metrics"""
    quality = {
        'consensus_score': 0,
        'confidence_score': 0,
        'completeness_score': 0,
        'overall': 0,
        'label': '',
        'description': ''
    }
    
    # Consensus score (based on approval rate)
    quality['consensus_score'] = result.approval_rate * 5
    
    # Confidence score (based on number of approvals vs rejections)
    approve_count = sum(1 for v in result.votes if v.vote.value == "approve")
    total = len(result.votes)
    if total > 0:
        quality['confidence_score'] = (approve_count / total) * 5
    
    # Completeness score (has trade plan, votes, etc.)
    completeness = 0
    if result.trade_plan:
        completeness += 2
        if result.trade_plan.trades:
            completeness += 1
    if result.votes:
        completeness += 1
    if result.approved:
        completeness += 1
    quality['completeness_score'] = completeness
    
    # Overall quality
    quality['overall'] = (quality['consensus_score'] * 0.4 + 
                         quality['confidence_score'] * 0.3 + 
                         quality['completeness_score'] * 0.3)
    
    # Label and description
    if quality['overall'] >= 4.5:
        quality['label'] = 'Excellent'
        quality['description'] = 'Strong consensus with high-quality recommendations'
    elif quality['overall'] >= 3.5:
        quality['label'] = 'Good'
        quality['description'] = 'Solid agreement with actionable recommendations'
    elif quality['overall'] >= 2.5:
        quality['label'] = 'Fair'
        quality['description'] = 'Partial consensus - review agent concerns carefully'
    elif quality['overall'] >= 1.5:
        quality['label'] = 'Needs Review'
        quality['description'] = 'Low agreement - consider adjusting strategy or constraints'
    else:
        quality['label'] = 'Poor'
        quality['description'] = 'Agents could not agree - significant conflicts exist'
    
    return quality


def get_confidence_level(score: float) -> str:
    """Get confidence level class for styling"""
    if score >= 4:
        return 'high'
    elif score >= 2.5:
        return 'medium'
    else:
        return 'low'


# Initialize session state
def init_session_state():
    """Initialize all session state variables"""
    if 'memory' not in st.session_state:
        st.session_state.memory = ConversationMemory(window_size=50)
    if 'logger' not in st.session_state:
        st.session_state.logger = get_logger()
    if 'progress_log' not in st.session_state:
        st.session_state.progress_log = []
    if 'selected_strategy' not in st.session_state:
        st.session_state.selected_strategy = None
    if 'portfolio_parsed' not in st.session_state:
        st.session_state.portfolio_parsed = False


def create_sample_portfolio() -> Portfolio:
    """Create sample portfolio"""
    from demo import create_sample_portfolio as demo_portfolio
    return demo_portfolio()


def display_strategy_selector():
    """Display strategy selection interface after portfolio parsing"""
    st.subheader("🎯 Select Optimization Strategy")
    st.info("Choose how you want the swarm agents to optimize your portfolio. Each strategy has different priorities and risk tolerance.")
    
    # Strategy cards
    strategies = list_available_strategies()
    
    cols = st.columns(2)
    
    for idx, strategy_info in enumerate(strategies):
        col = cols[idx % 2]
        with col:
            strategy_type = StrategyType(strategy_info['type'])
            strategy = get_strategy(strategy_type)
            
            # Create selectable card
            is_selected = (st.session_state.selected_strategy and 
                          st.session_state.selected_strategy.strategy_type == strategy_type)
            
            card_class = "strategy-card selected" if is_selected else "strategy-card"
            
            with st.container():
                st.markdown(f"""
                <div class="{card_class}">
                    <h4>{strategy.name}</h4>
                    <p style="color: #6b7280; font-size: 0.9rem;">{strategy.description}</p>
                    <div>
                        <span class="priority-badge priority-medium">Beta: {strategy.target_beta}</span>
                        <span class="priority-badge priority-{'high' if strategy_info['risk_level'] == 'High' else 'low' if strategy_info['risk_level'] == 'Low' else 'medium'}">
                            Risk: {strategy_info['risk_level']}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Select {strategy.name}", key=f"btn_{strategy_type.value}", 
                            type="primary" if is_selected else "secondary"):
                    st.session_state.selected_strategy = strategy
                    st.session_state.memory.set_strategy(strategy.name)
                    st.rerun()
    
    # Custom strategy builder
    st.divider()
    st.subheader("🔧 Or Create Custom Strategy")
    
    with st.expander("Build Custom Strategy"):
        custom_name = st.text_input("Strategy Name", "My Custom Strategy")
        custom_desc = st.text_area("Description", "Custom optimization strategy")
        
        base_strategy = st.selectbox(
            "Base Template",
            [s.value for s in StrategyType if s != StrategyType.CUSTOM]
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Risk Parameters**")
            target_beta = st.slider("Target Beta", 0.3, 2.0, 1.0, 0.1)
            max_drawdown = st.slider("Max Drawdown Tolerance", 0.05, 0.50, 0.20, 0.05)
            volatility_target = st.slider("Volatility Target", 0.05, 0.35, 0.15, 0.05)
        
        with col2:
            st.markdown("**Constraints**")
            max_position = st.slider("Max Position Size (%)", 5, 30, 20)
            max_sector = st.slider("Max Sector Concentration (%)", 15, 50, 30)
            min_esg = st.slider("Minimum ESG Score", 0, 100, 60)
        
        st.markdown("**Priority Weights (1-10)**")
        p_cols = st.columns(5)
        priorities = {}
        with p_cols[0]:
            priorities['growth'] = st.slider("Growth", 1, 10, 5)
        with p_cols[1]:
            priorities['risk'] = st.slider("Risk Mgmt", 1, 10, 5)
        with p_cols[2]:
            priorities['income'] = st.slider("Income", 1, 10, 5)
        with p_cols[3]:
            priorities['tax_efficiency'] = st.slider("Tax", 1, 10, 5)
        with p_cols[4]:
            priorities['esg'] = st.slider("ESG", 1, 10, 5)
        
        if st.button("Create Custom Strategy", type="primary"):
            custom_strategy = create_custom_strategy(
                name=custom_name,
                description=custom_desc,
                base_strategy=StrategyType(base_strategy),
                target_beta=target_beta,
                max_drawdown_tolerance=max_drawdown,
                volatility_target=volatility_target,
                max_position_size=max_position / 100,
                max_sector_concentration=max_sector / 100,
                min_esg_score=min_esg,
                priorities=priorities
            )
            st.session_state.selected_strategy = custom_strategy
            st.session_state.memory.set_strategy(custom_name)
            st.success(f"✅ Created custom strategy: {custom_name}")
            st.rerun()


def display_progress_visualization(progress_log: List[Dict]):
    """Display real-time progress of the optimization"""
    st.subheader("📊 Optimization Progress")
    
    if not progress_log:
        st.info("Progress will appear here during optimization...")
        return
    
    # Progress timeline
    for entry in progress_log[-10:]:  # Show last 10 entries
        icon = {
            "Initializing": "🚀",
            "Analyzing": "🔍",
            "Analysis": "📊",
            "Debate": "💬",
            "Proposals": "📋",
            "Voting": "🗳️",
            "Complete": "✅",
            "Fallback": "⚠️",
            "Stopped": "🛑"
        }.get(entry['phase'], "▶️")
        
        status_class = "complete" if entry['phase'] == "Complete" else "active" if entry == progress_log[-1] else ""
        
        st.markdown(f"""
        <div class="progress-step {status_class}">
            <span style="font-size: 1.2rem; margin-right: 0.5rem;">{icon}</span>
            <div>
                <strong>Iteration {entry['iteration']}: {entry['phase']}</strong>
                <span style="color: #6b7280; font-size: 0.9rem;"> - {entry['details']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


def display_agent_flow_graph(result):
    """Display agent interaction flow as a simple visualization"""
    st.subheader("🔄 Agent Interaction Flow")
    
    if not result or not result.votes:
        return
    
    # Create a simple flow visualization using columns
    agent_order = ["Market Analysis", "Risk Assessment", "Tax Strategy", "ESG Compliance", "Algorithmic Trading"]
    
    cols = st.columns(len(result.votes))
    
    for idx, vote in enumerate(result.votes):
        agent_name = vote.agent_type.value.replace('_', ' ').title()
        vote_symbol = "✅" if vote.vote.value == "approve" else "❌"
        vote_color = "#22c55e" if vote.vote.value == "approve" else "#ef4444"
        
        with cols[idx]:
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: white; border-radius: 8px; border: 2px solid {vote_color};">
                <div style="font-size: 2rem;">{vote_symbol}</div>
                <div style="font-weight: bold; font-size: 0.9rem;">{agent_name}</div>
                <div style="font-size: 0.8rem; color: #6b7280;">{vote.vote.value.upper()}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Draw arrow to next (except last)
            if idx < len(result.votes) - 1:
                st.markdown("<div style='text-align: center;'>→</div>", unsafe_allow_html=True)


def export_results(result, orchestrator, portfolio, format: str) -> str:
    """Export results in specified format"""
    if format == "json":
        data = {
            "timestamp": datetime.now().isoformat(),
            "consensus": result.approved,
            "approval_rate": result.approval_rate,
            "iterations": result.iteration + 1,
            "portfolio": {
                "total_value": portfolio.total_value,
                "positions": len(portfolio.positions),
                "cash": portfolio.cash
            },
            "votes": [
                {
                    "agent": v.agent_type.value,
                    "vote": v.vote.value,
                    "rationale": v.rationale
                }
                for v in result.votes
            ],
            "trade_plan": None
        }
        
        if result.trade_plan:
            data["trade_plan"] = {
                "trades": [
                    {
                        "action": t.action,
                        "ticker": t.ticker,
                        "shares": t.shares,
                        "price": t.estimated_price,
                        "value": t.notional_value,
                        "rationale": t.rationale
                    }
                    for t in result.trade_plan.trades
                ],
                "tax_liability": result.trade_plan.expected_tax_liability,
                "execution_cost": result.trade_plan.expected_execution_cost,
                "timeline_days": result.trade_plan.execution_timeline_days
            }
        
        return json.dumps(data, indent=2)
    
    elif format == "csv":
        lines = ["Metric,Value"]
        lines.append(f"Timestamp,{datetime.now().isoformat()}")
        lines.append(f"Consensus,{result.approved}")
        lines.append(f"Approval Rate,{result.approval_rate:.2%}")
        lines.append(f"Iterations,{result.iteration + 1}")
        lines.append(f"Portfolio Value,{portfolio.total_value:.2f}")
        lines.append("")
        lines.append("Agent,Vote,Rationale")
        for v in result.votes:
            rationale_clean = v.rationale.replace(',', ';').replace('\n', ' ')[:100]
            lines.append(f"{v.agent_type.value},{v.vote.value},{rationale_clean}")
        
        if result.trade_plan:
            lines.append("")
            lines.append("Action,Ticker,Shares,Price,Value")
            for t in result.trade_plan.trades:
                lines.append(f"{t.action},{t.ticker},{t.shares},{t.estimated_price:.2f},{t.notional_value:.2f}")
        
        return "\n".join(lines)
    
    else:  # text
        return orchestrator.get_debate_summary()


def display_query_templates():
    """Display available query templates"""
    st.subheader("💬 Quick Actions")
    
    cols = st.columns(3)
    
    templates = [
        ("optimize", "🚀 Optimize Portfolio", {}),
        ("analyze_risk", "📊 Analyze Risk", {}),
        ("tax_harvest", "💰 Tax Harvest", {}),
        ("esg_check", "🌱 ESG Check", {}),
        ("sector_analysis", "📈 Sector Analysis", {}),
        ("compliance_check", "✅ Compliance", {})
    ]
    
    for idx, (template_name, label, params) in enumerate(templates):
        col = cols[idx % 3]
        with col:
            if st.button(label, key=f"tmpl_{template_name}"):
                template = QUERY_TEMPLATES.get(template_name, "")
                if template:
                    st.session_state.current_query = template.format(**params) if params else template
                    st.rerun()


def main():
    """Main enhanced Streamlit app"""
    init_session_state()
    
    # Header
    st.markdown('<div class="main-header">🤖 Portfolio Swarm Optimizer Pro</div>', unsafe_allow_html=True)
    
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
        require_unanimous = st.checkbox("Require Unanimous Approval", False)
        
        st.divider()
        
        # Agent selection
        st.subheader("Active Agents")
        use_market = st.checkbox("Market Analysis", True)
        use_risk = st.checkbox("Risk Assessment", True)
        use_tax = st.checkbox("Tax Strategy", True)
        use_esg = st.checkbox("ESG Compliance", True)
        use_trading = st.checkbox("Algorithmic Trading", True)
        
        st.divider()
        
        # Session info
        if st.session_state.selected_strategy:
            st.success(f"Strategy: {st.session_state.selected_strategy.name}")
        
        # Clear button
        if st.button("🗑️ Clear All"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            init_session_state()
            st.rerun()
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Portfolio", 
        "🎯 Strategy", 
        "🤖 Optimize", 
        "📈 Results",
        "📖 Docs"
    ])
    
    # Tab 1: Portfolio Input
    with tab1:
        if portfolio_source == "Sample Portfolio ($50M)":
            if st.button("Load Sample Portfolio"):
                st.session_state.portfolio = create_sample_portfolio()
                st.session_state.portfolio_parsed = True
                # Clear previous results
                if 'result' in st.session_state:
                    del st.session_state.result
                st.success("✅ Sample portfolio loaded! Now select a strategy in the Strategy tab.")
        
        elif portfolio_source == "Text Description":
            st.subheader("📝 Describe Your Portfolio")
            
            with st.expander("📖 Example Formats"):
                st.code("""I own 10,000 shares of Apple (AAPL) at $185, bought at $150.
Also 5,000 Microsoft shares at $410 (cost basis $350).
Cash: $500,000. Keep tech under 30%.""", language="text")
            
            portfolio_text = st.text_area(
                "Describe your portfolio:",
                height=150,
                placeholder="Example: 10,000 AAPL at $185..."
            )
            
            if st.button("🔍 Parse Portfolio") and portfolio_text:
                try:
                    from portfolio_swarm.text_parser import parse_portfolio_text
                    portfolio = parse_portfolio_text(portfolio_text)
                    st.session_state.portfolio = portfolio
                    st.session_state.portfolio_parsed = True
                    
                    # Clear previous results
                    if 'result' in st.session_state:
                        del st.session_state.result
                    
                    st.success(f"✅ Parsed {len(portfolio.positions)} positions! Select a strategy in the Strategy tab.")
                except Exception as e:
                    st.error(f"❌ Parse error: {e}")
        
        elif portfolio_source == "Upload File":
            uploaded = st.file_uploader("Upload CSV/JSON/YAML", type=['csv', 'json', 'yaml'])
            if uploaded:
                try:
                    from portfolio_swarm.input_parser import PortfolioParser
                    import tempfile, os
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded.name)[1]) as tmp:
                        tmp.write(uploaded.getvalue())
                        tmp_path = tmp.name
                    
                    parser = PortfolioParser()
                    portfolio = parser.parse_file(tmp_path)
                    os.unlink(tmp_path)
                    
                    st.session_state.portfolio = portfolio
                    st.session_state.portfolio_parsed = True
                    st.success(f"✅ Loaded from {uploaded.name}! Select a strategy.")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        elif portfolio_source == "Custom Portfolio":
            st.subheader("Build Custom Portfolio")
            
            if 'positions' not in st.session_state:
                st.session_state.positions = []
            
            with st.form("add_position"):
                col1, col2 = st.columns(2)
                with col1:
                    ticker = st.text_input("Ticker", "AAPL").upper()
                    shares = st.number_input("Shares", 1, value=1000)
                    price = st.number_input("Current Price", 0.01, value=150.0)
                    cost = st.number_input("Cost Basis", 0.01, value=140.0)
                with col2:
                    days = st.number_input("Days Held", 1, value=400)
                    sector = st.selectbox("Sector", ["Technology", "Healthcare", "Financials", "Consumer Staples", "Energy"])
                    esg = st.slider("ESG Score", 0, 100, 70)
                    beta = st.number_input("Beta", 0.1, 3.0, 1.0)
                
                if st.form_submit_button("Add Position"):
                    pos = Position(
                        ticker=ticker, shares=shares, current_price=price, cost_basis=cost,
                        acquisition_date=datetime.now() - timedelta(days=days),
                        sector=sector, esg_score=esg, beta=beta
                    )
                    st.session_state.positions.append(pos)
                    st.success(f"Added {ticker}")
            
            if st.session_state.positions:
                st.dataframe(pd.DataFrame([
                    {"Ticker": p.ticker, "Shares": p.shares, "Value": f"${p.market_value:,.0f}"}
                    for p in st.session_state.positions
                ]))
                
                cash = st.number_input("Cash Balance", 0.0, value=1000000.0)
                if st.button("Create Portfolio"):
                    st.session_state.portfolio = Portfolio(
                        positions=st.session_state.positions,
                        cash=cash,
                        policy_limits={"technology_limit": 30.0}
                    )
                    st.session_state.portfolio_parsed = True
                    st.success("✅ Portfolio created! Now select a strategy.")
        
        # Show portfolio summary if loaded
        if 'portfolio' in st.session_state:
            st.divider()
            st.subheader("📊 Portfolio Summary")
            p = st.session_state.portfolio
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Value", f"${p.total_value:,.0f}")
            col2.metric("Beta", f"{p.portfolio_beta:.2f}")
            col3.metric("ESG Score", f"{p.average_esg_score:.1f}")
            col4.metric("Positions", len(p.positions))
            
            # Sector chart
            sector_df = pd.DataFrame({
                'Sector': list(p.sector_allocation.keys()),
                'Allocation': list(p.sector_allocation.values())
            })
            st.bar_chart(sector_df.set_index('Sector'))
    
    # Tab 2: Strategy Selection (only shown after portfolio is parsed)
    with tab2:
        if not st.session_state.portfolio_parsed:
            st.warning("⚠️ Please load a portfolio first in the Portfolio tab")
        else:
            display_strategy_selector()
            
            # Show selected strategy details
            if st.session_state.selected_strategy:
                st.divider()
                st.success(f"✅ Selected: **{st.session_state.selected_strategy.name}**")
                
                strategy = st.session_state.selected_strategy
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Risk Parameters**")
                    st.write(f"- Target Beta: {strategy.target_beta}")
                    st.write(f"- Max Drawdown: {strategy.max_drawdown_tolerance:.0%}")
                    st.write(f"- Volatility Target: {strategy.volatility_target:.0%}")
                
                with col2:
                    st.markdown("**Constraints**")
                    st.write(f"- Max Position: {strategy.max_position_size:.0%}")
                    st.write(f"- Max Sector: {strategy.max_sector_concentration:.0%}")
                    st.write(f"- Min ESG: {strategy.min_esg_score}")
                
                st.info("👉 Go to the Optimize tab to run optimization with this strategy!")
    
    # Tab 3: Optimization
    with tab3:
        if 'portfolio' not in st.session_state:
            st.warning("⚠️ Please load a portfolio first")
        elif not st.session_state.selected_strategy:
            st.warning("⚠️ Please select a strategy in the Strategy tab")
        else:
            portfolio = st.session_state.portfolio
            strategy = st.session_state.selected_strategy
            
            st.subheader("🚀 Run Swarm Optimization")
            
            # Configuration summary
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                **Portfolio:** ${portfolio.total_value:,.0f} ({len(portfolio.positions)} positions)
                
                **Strategy:** {strategy.name}
                """)
            with col2:
                st.markdown(f"""
                **Swarm Config:**
                - Max Iterations: {max_iterations}
                - Consensus: {consensus_threshold:.0%}
                - Agents: {sum([use_market, use_risk, use_tax, use_esg, use_trading])}
                """)
            
            # Progress placeholder
            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            
            if st.button("🚀 Start Optimization", type="primary"):
                # Progress callback
                def progress_callback(iteration, phase, details):
                    st.session_state.progress_log.append({
                        "iteration": iteration,
                        "phase": phase,
                        "details": details,
                        "time": datetime.now().strftime("%H:%M:%S")
                    })
                    with progress_placeholder.container():
                        display_progress_visualization(st.session_state.progress_log)
                    status_placeholder.info(f"🔄 {phase}: {details}")
                
                # Clear previous progress
                st.session_state.progress_log = []
                
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
                
                # Create orchestrator with strategy
                orchestrator = SwarmOrchestrator(
                    agents=agents,
                    max_iterations=max_iterations,
                    consensus_threshold=consensus_threshold,
                    require_unanimous=require_unanimous,
                    progress_callback=progress_callback,
                    strategy=strategy
                )
                
                # Run optimization
                result = orchestrator.run_rebalancing_swarm(portfolio)
                
                # Store results
                st.session_state.result = result
                st.session_state.orchestrator = orchestrator
                
                status_placeholder.success("✅ Optimization complete!")
                st.balloons()
    
    # Tab 4: Results
    with tab4:
        if 'result' not in st.session_state:
            st.info("ℹ️ Run optimization first")
        else:
            result = st.session_state.result
            orchestrator = st.session_state.orchestrator
            portfolio = st.session_state.portfolio
            strategy = st.session_state.selected_strategy
            
            # Calculate quality score
            quality = get_result_quality_score(result, strategy)
            
            # Overall Score Card (prominent display)
            st.markdown(f"""
            <div class="overall-score">
                <div class="score-text">{quality['label']} Result</div>
                <div class="stars">{get_stars(quality['overall'])}</div>
                <div class="score-description">{quality['description']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Summary header
            if result.approved:
                st.success(f"🎉 Consensus Achieved! ({result.approval_rate:.0%} approval)")
            else:
                st.warning(f"⚠️ No Consensus ({result.approval_rate:.0%} approval)")
            
            # Detailed Quality Metrics with Stars
            st.subheader("📊 Quality Breakdown")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="rating-card">
                    <div class="rating-header">
                        <span class="rating-label">Consensus</span>
                    </div>
                    <div>{get_stars_html(quality['consensus_score'])}</div>
                    <div class="rating-description">{result.approval_rate:.0%} agent agreement</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="rating-card">
                    <div class="rating-header">
                        <span class="rating-label">Confidence</span>
                    </div>
                    <div>{get_stars_html(quality['confidence_score'])}</div>
                    <div class="rating-description">Agent conviction level</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="rating-card">
                    <div class="rating-header">
                        <span class="rating-label">Completeness</span>
                    </div>
                    <div>{get_stars_html(quality['completeness_score'])}</div>
                    <div class="rating-description">Result thoroughness</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="rating-card">
                    <div class="rating-header">
                        <span class="rating-label">Overall</span>
                    </div>
                    <div>{get_stars_html(quality['overall'])}</div>
                    <div class="rating-description">{quality['label']}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Performance metrics
            st.divider()
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Approval Rate", f"{result.approval_rate:.0%}")
            col2.metric("Iterations", f"{result.iteration + 1}")
            col3.metric("Messages", len(orchestrator.comm_bus.messages))
            col4.metric("Strategy", strategy.name if strategy else "N/A")
            
            st.divider()
            
            # Agent flow visualization
            display_agent_flow_graph(result)
            
            st.divider()
            
            # Agent votes with confidence ratings
            st.subheader("🗳️ Agent Votes & Confidence")
            
            for vote in result.votes:
                vote_class = "vote-approve" if vote.vote.value == "approve" else "vote-reject"
                symbol = "✅" if vote.vote.value == "approve" else "❌"
                agent_name = vote.agent_type.value.replace('_', ' ').title()
                
                # Calculate agent confidence from rationale length and keywords
                confidence_score = 3.5  # Base confidence
                rationale_lower = vote.rationale.lower()
                if any(word in rationale_lower for word in ['strongly', 'confident', 'clearly', 'definitely']):
                    confidence_score += 1
                if any(word in rationale_lower for word in ['concern', 'risk', 'caution', 'uncertain']):
                    confidence_score -= 0.5
                if vote.vote.value == "approve":
                    confidence_score += 0.5
                confidence_score = min(5, max(1, confidence_score))
                
                confidence_level = get_confidence_level(confidence_score)
                stars = get_stars(confidence_score)
                
                st.markdown(f"""
                <div class="agent-vote {vote_class}">
                    <div class="trade-header">
                        <strong>{symbol} {agent_name}</strong>
                        <span class="star-rating" title="Agent Confidence">{stars}</span>
                    </div>
                    <p>{vote.rationale}</p>
                    <div class="confidence-bar">
                        <div class="confidence-fill confidence-{confidence_level}" style="width: {confidence_score * 20}%"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.divider()
            
            # Trade plan with ratings
            st.subheader("📋 Trade Recommendations")
            if result.trade_plan and result.trade_plan.trades:
                
                # Sort trades by score for better presentation
                trades_with_scores = []
                for trade in result.trade_plan.trades:
                    scores = calculate_trade_score(trade, strategy)
                    trades_with_scores.append((trade, scores))
                
                # Sort by overall score descending
                trades_with_scores.sort(key=lambda x: x[1]['overall'], reverse=True)
                
                for trade, scores in trades_with_scores:
                    action_class = "trade-action-buy" if trade.action == "BUY" else "trade-action-sell"
                    stars = get_stars(scores['overall'])
                    confidence_level = get_confidence_level(scores['overall'])
                    
                    st.markdown(f"""
                    <div class="trade-card">
                        <div class="trade-header">
                            <div>
                                <span class="{action_class}">{trade.action}</span>
                                <strong style="margin-left: 0.5rem; font-size: 1.1rem;">{trade.ticker}</strong>
                            </div>
                            <span class="star-rating" title="Trade Rating">{stars}</span>
                        </div>
                        <div style="margin-top: 0.75rem; display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
                            <div>
                                <div style="color: #6b7280; font-size: 0.8rem;">Shares</div>
                                <div style="font-weight: 600;">{trade.shares:,}</div>
                            </div>
                            <div>
                                <div style="color: #6b7280; font-size: 0.8rem;">Est. Price</div>
                                <div style="font-weight: 600;">${trade.estimated_price:.2f}</div>
                            </div>
                            <div>
                                <div style="color: #6b7280; font-size: 0.8rem;">Value</div>
                                <div style="font-weight: 600;">${trade.notional_value:,.0f}</div>
                            </div>
                        </div>
                        <div style="margin-top: 0.75rem; padding: 0.5rem; background: #f8fafc; border-radius: 4px;">
                            <div style="color: #6b7280; font-size: 0.8rem;">Rationale</div>
                            <div style="font-size: 0.9rem;">{trade.rationale}</div>
                        </div>
                        <div class="confidence-bar">
                            <div class="confidence-fill confidence-{confidence_level}" style="width: {scores['overall'] * 20}%"></div>
                        </div>
                        <div style="margin-top: 0.5rem; font-size: 0.75rem; color: #9ca3af;">
                            Value: {get_stars(scores['value_score'])} | 
                            Risk: {get_stars(scores['risk_score'])} | 
                            Strategy Fit: {get_stars(scores['alignment_score'])}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.divider()
                
                # Trade plan summary metrics
                st.subheader("💰 Trade Plan Summary")
                col1, col2, col3 = st.columns(3)
                col1.metric("Tax Liability", f"${result.trade_plan.expected_tax_liability:,.0f}")
                col2.metric("Execution Cost", f"${result.trade_plan.expected_execution_cost:,.0f}")
                col3.metric("Timeline", f"{result.trade_plan.execution_timeline_days} days")
            else:
                st.warning("No trade plan generated")
            
            st.divider()
            
            # Legend for understanding ratings
            with st.expander("ℹ️ Understanding Star Ratings"):
                st.markdown("""
                ### What the Stars Mean
                
                | Rating | Stars | Meaning |
                |--------|-------|---------|
                | ★★★★★ | Excellent | Highest confidence/quality |
                | ★★★★☆ | Good | Strong recommendation |
                | ★★★☆☆ | Fair | Acceptable, review carefully |
                | ★★☆☆☆ | Poor | Concerns exist, proceed with caution |
                | ★☆☆☆☆ | Very Poor | Not recommended |
                
                ### Rating Categories
                
                - **Consensus**: How well agents agreed on the recommendation
                - **Confidence**: Overall conviction level of the agents
                - **Completeness**: How thorough the analysis was
                - **Value Score**: Impact/significance of the trade
                - **Risk Score**: Risk assessment quality
                - **Strategy Fit**: How well trade aligns with your selected strategy
                """)
            
            st.divider()
            
            # Export options
            st.subheader("📥 Export Results")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                json_data = export_results(result, orchestrator, portfolio, "json")
                st.download_button(
                    "📄 Download JSON",
                    json_data,
                    f"swarm_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    "application/json"
                )
            
            with col2:
                csv_data = export_results(result, orchestrator, portfolio, "csv")
                st.download_button(
                    "📊 Download CSV",
                    csv_data,
                    f"swarm_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv"
                )
            
            with col3:
                text_data = export_results(result, orchestrator, portfolio, "text")
                st.download_button(
                    "📝 Download Report",
                    text_data,
                    f"swarm_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    "text/plain"
                )
    
    # Tab 5: Documentation
    with tab5:
        st.header("📖 Documentation")
        
        st.markdown("""
        ## 🎯 Optimization Strategies
        
        Choose from pre-built strategies or create your own:
        
        | Strategy | Risk Level | Focus |
        |----------|-----------|-------|
        | Aggressive Growth | High | Capital appreciation, momentum |
        | Conservative Income | Low | Dividends, stability |
        | Balanced | Medium | Diversification |
        | Tax Efficient | Medium | Loss harvesting, long-term gains |
        | ESG Focused | Medium | Sustainability, exclusions |
        | Risk Minimization | Low | Defensive, hedging |
        
        ## 🔄 Workflow
        
        1. **Portfolio Tab**: Load or create your portfolio
        2. **Strategy Tab**: Select optimization strategy
        3. **Optimize Tab**: Run swarm optimization
        4. **Results Tab**: View results and export
        
        ## 🤖 Agent Roles
        
        - **Market Analysis**: Valuation, trends, sentiment
        - **Risk Assessment**: Compliance, concentration, VaR
        - **Tax Strategy**: Capital gains, loss harvesting
        - **ESG Compliance**: Sustainability scores, exclusions
        - **Algorithmic Trading**: Execution feasibility, costs
        
        ## 📊 Export Formats
        
        - **JSON**: Complete structured data
        - **CSV**: Spreadsheet-friendly format
        - **Text**: Human-readable report
        """)


if __name__ == "__main__":
    main()
