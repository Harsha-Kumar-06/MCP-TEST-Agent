"""
Drayvn Agents - Streamlit Deployment & Marketplace Registration Script

This script helps you:
1. Deploy agents to Streamlit Cloud
2. Register demo URLs in Drayvn Marketplace

Usage:
    python deploy_streamlit_agents.py --register-all
    python deploy_streamlit_agents.py --list
    python deploy_streamlit_agents.py --update <agent_id> <streamlit_url>
"""

import os
import sys
import json
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Configuration
DRAYVN_API = os.getenv("DRAYVN_API_URL", "https://your-drayvn-server.com/api/v1")
AUTH_TOKEN = os.getenv("DRAYVN_AUTH_TOKEN", "your-auth-token")

# Agent definitions - Update these after deploying to Streamlit Cloud
AGENTS = [
    {
        "id": None,  # Fill with marketplace agent ID after creation
        "name": "access-controller-agent",
        "display_name": "Access Controller Agent",
        "description": "AI-powered organizational access authority for Atlassian & GitHub",
        "folder": "access_controller_agent",
        "streamlit_url": None,  # Fill after deploying: https://access-controller.streamlit.app
        "icon": "🔐",
        "category": "DevOps",
        "pattern": "Hierarchical ADK"
    },
    {
        "id": None,
        "name": "campaign-validator-agent",
        "display_name": "Campaign Validator Agent",
        "description": "Validates influencer posts against brand campaign requirements with HITL",
        "folder": "campaign_validator_agent",
        "main_file": "app.py",  # Uses existing app.py
        "streamlit_url": None,
        "icon": "🎯",
        "category": "Marketing",
        "pattern": "Human-in-the-Loop"
    },
    {
        "id": None,
        "name": "portfolio-manager-agent",
        "display_name": "Portfolio Manager",
        "description": "AI investment agent creating personalized, data-driven portfolios",
        "folder": "portfolio_manager",
        "streamlit_url": None,
        "icon": "📈",
        "category": "Finance",
        "pattern": "Sequential Pipeline"
    },
    {
        "id": None,
        "name": "pr-code-reviewer-agent",
        "display_name": "PR Code Reviewer",
        "description": "AI Senior Lead Developer performing 5-point code inspection",
        "folder": "pr_code_reviewer",
        "streamlit_url": None,
        "icon": "🔍",
        "category": "DevOps",
        "pattern": "Parallel Swarm"
    },
    {
        "id": None,
        "name": "research-assistant-agent",
        "display_name": "Research Assistant",
        "description": "Document analysis with 5-agent sequential pipeline",
        "folder": "research_assistant",
        "streamlit_url": None,
        "icon": "🔬",
        "category": "Research",
        "pattern": "Sequential Pipeline"
    },
    {
        "id": None,
        "name": "loan-underwriter-agent",
        "display_name": "Loan Underwriter",
        "description": "20x faster mortgage processing with Fan-Out/Fan-In architecture",
        "folder": "FAN out-FAN in",
        "streamlit_url": None,
        "icon": "🏦",
        "category": "Finance",
        "pattern": "Fan-Out/Fan-In"
    },
    {
        "id": None,
        "name": "content-moderator-agent",
        "display_name": "Content Moderator",
        "description": "AI Compliance Officer for social media content moderation",
        "folder": "social_media_content_moderation",
        "streamlit_url": None,
        "icon": "🛡️",
        "category": "Content",
        "pattern": "Parallel Swarm"
    },
    {
        "id": None,
        "name": "helpdesk-bot-agent",
        "display_name": "HelpDesk Bot",
        "description": "AI-powered internal support with Router Pattern routing to specialists",
        "folder": "Router Pattern",
        "streamlit_url": None,
        "icon": "🤖",
        "category": "Enterprise",
        "pattern": "Router Pattern"
    },
    {
        "id": None,
        "name": "social-media-trends-agent",
        "display_name": "Social Media Trends Agent",
        "description": "Trend intelligence across Instagram, TikTok, and YouTube",
        "folder": "social_media_marketing",
        "streamlit_url": None,
        "icon": "📱",
        "category": "Marketing",
        "pattern": "Single Agent"
    },
    {
        "id": None,
        "name": "portfolio-swarm-agent",
        "display_name": "Portfolio Swarm Optimizer",
        "description": "5-agent collaborative system for portfolio optimization",
        "folder": "Swarm Pattern",
        "streamlit_url": None,
        "icon": "🐝",
        "category": "Finance",
        "pattern": "Swarm Pattern"
    }
]


def list_agents():
    """List all configured agents and their status."""
    print("\n📦 Drayvn Agent Inventory\n" + "=" * 50)
    
    for agent in AGENTS:
        status = "✅" if agent["streamlit_url"] else "❌"
        registered = "✅" if agent["id"] else "❌"
        
        print(f"""
{agent['icon']} {agent['display_name']}
   Folder: {agent['folder']}
   Streamlit URL: {status} {agent['streamlit_url'] or 'Not deployed'}
   Marketplace ID: {registered} {agent['id'] or 'Not registered'}
   Category: {agent['category']} | Pattern: {agent['pattern']}
""")


def update_marketplace_agent(agent_id: str, demo_url: str):
    """Update agent's demo URL in marketplace."""
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.put(
            f"{DRAYVN_API}/agent-marketplace/{agent_id}",
            json={"demoUrl": demo_url},
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"✅ Successfully updated agent {agent_id} with demo URL: {demo_url}")
            return True
        else:
            print(f"❌ Failed to update agent: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False


def register_all_agents():
    """Register all agents that have Streamlit URLs configured."""
    print("\n🚀 Registering Demo URLs in Marketplace\n" + "=" * 50)
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for agent in AGENTS:
        if not agent["id"]:
            print(f"⏭️  {agent['display_name']}: No marketplace ID configured")
            skip_count += 1
            continue
            
        if not agent["streamlit_url"]:
            print(f"⏭️  {agent['display_name']}: No Streamlit URL configured")
            skip_count += 1
            continue
        
        print(f"📤 Updating {agent['display_name']}...")
        if update_marketplace_agent(agent["id"], agent["streamlit_url"]):
            success_count += 1
        else:
            fail_count += 1
    
    print(f"""
📊 Registration Summary
   ✅ Success: {success_count}
   ⏭️  Skipped: {skip_count}
   ❌ Failed: {fail_count}
""")


def generate_streamlit_deployment_guide():
    """Generate deployment commands for each agent."""
    print("\n📖 Streamlit Cloud Deployment Guide (Bitbucket)\n" + "=" * 50)
    
    print("""
Step 1: Push your repo to Bitbucket (if not already)
   git add .
   git commit -m "Add Streamlit demos for all agents"
   git push origin main

Step 2: Go to https://share.streamlit.io

Step 3: Click "New app" → Connect Bitbucket account

Step 4: Deploy each agent:
""")
    
    for agent in AGENTS:
        main_file = agent.get('main_file', 'streamlit_app.py')
        print(f"""
{agent['icon']} {agent['display_name']}
   Repository: bitbucket.org/your-workspace/drayvn_agents
   Branch: main
   Main file path: {agent['folder']}/{main_file}
   
   Expected URL: https://{agent['name']}.streamlit.app
""")


def save_config():
    """Save current agent configuration to JSON."""
    config_path = Path(__file__).parent / "agents_config.json"
    
    with open(config_path, "w") as f:
        json.dump(AGENTS, f, indent=2)
    
    print(f"✅ Configuration saved to {config_path}")


def load_config():
    """Load agent configuration from JSON."""
    config_path = Path(__file__).parent / "agents_config.json"
    
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    return AGENTS


def main():
    parser = argparse.ArgumentParser(
        description="Deploy Drayvn agents to Streamlit and register with marketplace"
    )
    
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all configured agents"
    )
    
    parser.add_argument(
        "--register-all", "-r",
        action="store_true",
        help="Register all agents with marketplace"
    )
    
    parser.add_argument(
        "--update", "-u",
        nargs=2,
        metavar=("AGENT_ID", "STREAMLIT_URL"),
        help="Update a single agent's demo URL"
    )
    
    parser.add_argument(
        "--guide", "-g",
        action="store_true",
        help="Show Streamlit Cloud deployment guide"
    )
    
    parser.add_argument(
        "--save-config", "-s",
        action="store_true",
        help="Save current configuration to JSON"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_agents()
    elif args.register_all:
        register_all_agents()
    elif args.update:
        update_marketplace_agent(args.update[0], args.update[1])
    elif args.guide:
        generate_streamlit_deployment_guide()
    elif args.save_config:
        save_config()
    else:
        parser.print_help()
        print("\n💡 Quick start: python deploy_streamlit_agents.py --guide")


if __name__ == "__main__":
    main()
