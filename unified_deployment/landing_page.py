"""
Drayvn Agents - Landing Page
All AI Agents in One Place
"""

import streamlit as st

st.set_page_config(
    page_title="Drayvn AI Agents",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .agent-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        color: white;
        transition: transform 0.3s ease;
    }
    .agent-card:hover {
        transform: translateY(-5px);
    }
    .agent-icon {
        font-size: 48px;
        margin-bottom: 10px;
    }
    .agent-title {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .agent-desc {
        font-size: 14px;
        opacity: 0.9;
    }
    .pattern-badge {
        background: rgba(255,255,255,0.2);
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 12px;
        margin-top: 10px;
        display: inline-block;
    }
    .main-header {
        text-align: center;
        padding: 30px 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🤖 Drayvn AI Agents</h1>
    <p style="font-size: 18px; color: #666;">Enterprise-Ready AI Agent Marketplace Demo</p>
</div>
""", unsafe_allow_html=True)

# Agent definitions
agents = [
    {
        "name": "Access Controller",
        "icon": "🔐",
        "route": "/access-controller",
        "description": "AI-powered organizational access authority for Atlassian & GitHub. Manage user invitations and permissions.",
        "pattern": "Hierarchical ADK",
        "category": "DevOps"
    },
    {
        "name": "Portfolio Manager",
        "icon": "📈",
        "route": "/portfolio-manager",
        "description": "AI investment agent creating personalized, data-driven portfolios with risk management.",
        "pattern": "Sequential Pipeline",
        "category": "Finance"
    },
    {
        "name": "Campaign Validator",
        "icon": "🎯",
        "route": "/campaign-validator",
        "description": "Validates influencer posts against brand campaign requirements with Human-in-the-Loop approval.",
        "pattern": "Human-in-the-Loop",
        "category": "Marketing"
    },
    {
        "name": "PR Code Reviewer",
        "icon": "🔍",
        "route": "/pr-code-reviewer",
        "description": "AI Senior Lead Developer performing 5-point code inspection: logic, security, performance, style, testing.",
        "pattern": "Parallel Swarm",
        "category": "DevOps"
    },
    {
        "name": "Research Assistant",
        "icon": "🔬",
        "route": "/research-assistant",
        "description": "Document analysis with 5-agent sequential pipeline for comprehensive research synthesis.",
        "pattern": "Sequential Pipeline",
        "category": "Research"
    },
    {
        "name": "Loan Underwriter",
        "icon": "🏦",
        "route": "/loan-underwriter",
        "description": "20x faster mortgage processing with Fan-Out/Fan-In architecture for parallel risk assessment.",
        "pattern": "Fan-Out/Fan-In",
        "category": "Finance"
    },
    {
        "name": "Content Moderator",
        "icon": "🛡️",
        "route": "/content-moderator",
        "description": "AI Compliance Officer for social media content moderation with multi-aspect analysis.",
        "pattern": "Parallel Swarm",
        "category": "Content"
    },
    {
        "name": "HelpDesk Bot",
        "icon": "🤖",
        "route": "/helpdesk-bot",
        "description": "AI-powered internal support with Router Pattern routing to IT, HR, and Facilities specialists.",
        "pattern": "Router Pattern",
        "category": "Enterprise"
    },
    {
        "name": "Social Media Trends",
        "icon": "📱",
        "route": "/social-media-trends",
        "description": "Trend intelligence across Instagram, TikTok, and YouTube with engagement analysis.",
        "pattern": "Single Agent",
        "category": "Marketing"
    },
    {
        "name": "Portfolio Swarm",
        "icon": "🐝",
        "route": "/portfolio-swarm",
        "description": "5-agent collaborative system for portfolio optimization with market analysis and risk management.",
        "pattern": "Swarm Pattern",
        "category": "Finance"
    }
]

# Category colors
category_colors = {
    "DevOps": "#2196F3",
    "Finance": "#4CAF50",
    "Marketing": "#FF9800",
    "Research": "#9C27B0",
    "Content": "#E91E63",
    "Enterprise": "#00BCD4"
}

# Display agents in a grid
st.markdown("---")
st.subheader("🚀 Available Agents")

# Create 2-column grid
col1, col2 = st.columns(2)

for i, agent in enumerate(agents):
    col = col1 if i % 2 == 0 else col2
    
    with col:
        color = category_colors.get(agent["category"], "#667eea")
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {color} 0%, {color}99 100%); 
                    border-radius: 15px; padding: 20px; margin: 10px 0; color: white;">
            <div style="font-size: 48px;">{agent["icon"]}</div>
            <div style="font-size: 22px; font-weight: bold; margin: 10px 0;">{agent["name"]}</div>
            <div style="font-size: 14px; opacity: 0.9; margin-bottom: 15px;">{agent["description"]}</div>
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <span style="background: rgba(255,255,255,0.2); padding: 5px 12px; border-radius: 20px; font-size: 12px;">
                    {agent["pattern"]}
                </span>
                <span style="background: rgba(255,255,255,0.3); padding: 5px 12px; border-radius: 20px; font-size: 12px;">
                    {agent["category"]}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Open {agent['name']}", key=f"btn_{i}", use_container_width=True):
            st.markdown(f'<meta http-equiv="refresh" content="0;url={agent["route"]}">', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p>Built with ❤️ by Drayvn | Powered by Google AI</p>
    <p style="font-size: 12px;">Enterprise AI Agent Marketplace</p>
</div>
""", unsafe_allow_html=True)

# Sidebar with quick links
with st.sidebar:
    st.markdown("### 🔗 Quick Links")
    for agent in agents:
        st.markdown(f"[{agent['icon']} {agent['name']}]({agent['route']})")
    
    st.markdown("---")
    st.markdown("### 📊 Statistics")
    st.metric("Total Agents", len(agents))
    st.metric("Patterns", len(set(a["pattern"] for a in agents)))
    st.metric("Categories", len(set(a["category"] for a in agents)))
