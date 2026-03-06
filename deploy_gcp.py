"""
Google Cloud Run Deployment Script for Drayvn Agents

Prerequisites:
1. Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install
2. Login: gcloud auth login
3. Set project: gcloud config set project YOUR_PROJECT_ID
4. Enable APIs: gcloud services enable run.googleapis.com cloudbuild.googleapis.com

Usage:
    python deploy_gcp.py --list                    # List all agents
    python deploy_gcp.py --deploy portfolio_manager  # Deploy single agent
    python deploy_gcp.py --deploy-all              # Deploy all agents
"""

import os
import subprocess
import argparse
from pathlib import Path

# Configuration - UPDATE THESE
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-project-id")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")

# Agent definitions
AGENTS = [
    {"folder": "access_controller_agent", "service": "access-controller", "main": "streamlit_app.py"},
    {"folder": "campaign_validator_agent", "service": "campaign-validator", "main": "app.py"},
    {"folder": "portfolio_manager", "service": "portfolio-manager", "main": "streamlit_app.py"},
    {"folder": "pr_code_reviewer", "service": "pr-code-reviewer", "main": "streamlit_app.py"},
    {"folder": "research_assistant", "service": "research-assistant", "main": "streamlit_app.py"},
    {"folder": "FAN out-FAN in", "service": "loan-underwriter", "main": "streamlit_app.py"},
    {"folder": "social_media_content_moderation", "service": "content-moderator", "main": "streamlit_app.py"},
    {"folder": "Router Pattern", "service": "helpdesk-bot", "main": "streamlit_app.py"},
    {"folder": "social_media_marketing", "service": "social-media-trends", "main": "streamlit_app.py"},
    {"folder": "Swarm Pattern", "service": "portfolio-swarm", "main": "streamlit_app.py"},
]

BASE_DIR = Path(__file__).parent


def create_dockerfile(agent_folder: Path, main_file: str):
    """Create a Dockerfile for the agent."""
    dockerfile_content = f'''FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt* ./
RUN pip install --no-cache-dir streamlit requests python-dotenv || true
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

COPY . .

EXPOSE 8080

ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true

CMD ["streamlit", "run", "{main_file}", "--server.port=8080", "--server.address=0.0.0.0"]
'''
    
    dockerfile_path = agent_folder / "Dockerfile"
    with open(dockerfile_path, "w") as f:
        f.write(dockerfile_content)
    print(f"  Created Dockerfile for {main_file}")


def deploy_agent(agent: dict):
    """Deploy a single agent to Cloud Run."""
    folder = agent["folder"]
    service = agent["service"]
    main_file = agent["main"]
    
    agent_path = BASE_DIR / folder
    
    if not agent_path.exists():
        print(f"  ERROR: Folder not found: {folder}")
        return False
    
    print(f"\n{'='*50}")
    print(f"Deploying: {service}")
    print(f"  Folder: {folder}")
    print(f"  Main file: {main_file}")
    print(f"{'='*50}")
    
    # Create Dockerfile
    create_dockerfile(agent_path, main_file)
    
    # Deploy to Cloud Run
    cmd = [
        "gcloud", "run", "deploy", service,
        "--source", str(agent_path),
        "--region", GCP_REGION,
        "--platform", "managed",
        "--allow-unauthenticated",
        "--memory", "1Gi",
        "--timeout", "300",
        "--quiet"
    ]
    
    print(f"  Running: {' '.join(cmd[:6])}...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            # Extract URL from output
            url = f"https://{service}-{GCP_PROJECT_ID}.{GCP_REGION}.run.app"
            print(f"  SUCCESS: {url}")
            return True
        else:
            print(f"  FAILED: {result.stderr}")
            return False
    except FileNotFoundError:
        print("  ERROR: gcloud CLI not found. Install from https://cloud.google.com/sdk/docs/install")
        return False


def list_agents():
    """List all available agents."""
    print("\n" + "="*60)
    print(" Available Agents for Cloud Run Deployment")
    print("="*60)
    
    for agent in AGENTS:
        folder_path = BASE_DIR / agent["folder"]
        exists = "✅" if folder_path.exists() else "❌"
        print(f"""
{exists} {agent['service']}
   Folder: {agent['folder']}
   Main: {agent['main']}
   URL: https://{agent['service']}-PROJECT_ID.{GCP_REGION}.run.app
""")


def deploy_all():
    """Deploy all agents."""
    print("\n" + "="*60)
    print(" Deploying ALL Agents to Cloud Run")
    print("="*60)
    
    success = 0
    failed = 0
    
    for agent in AGENTS:
        if deploy_agent(agent):
            success += 1
        else:
            failed += 1
    
    print("\n" + "="*60)
    print(f" Deployment Summary")
    print(f"   Success: {success}")
    print(f"   Failed: {failed}")
    print("="*60)


def main():
    parser = argparse.ArgumentParser(description="Deploy Drayvn Agents to Google Cloud Run")
    parser.add_argument("--list", "-l", action="store_true", help="List all agents")
    parser.add_argument("--deploy", "-d", metavar="FOLDER", help="Deploy specific agent by folder name")
    parser.add_argument("--deploy-all", "-a", action="store_true", help="Deploy all agents")
    parser.add_argument("--project", "-p", help="GCP Project ID")
    parser.add_argument("--region", "-r", help="GCP Region")
    
    args = parser.parse_args()
    
    global GCP_PROJECT_ID, GCP_REGION
    if args.project:
        GCP_PROJECT_ID = args.project
    if args.region:
        GCP_REGION = args.region
    
    if args.list:
        list_agents()
    elif args.deploy:
        agent = next((a for a in AGENTS if a["folder"] == args.deploy or a["service"] == args.deploy), None)
        if agent:
            deploy_agent(agent)
        else:
            print(f"Agent not found: {args.deploy}")
            print("Use --list to see available agents")
    elif args.deploy_all:
        deploy_all()
    else:
        parser.print_help()
        print("\n💡 Quick start:")
        print("   1. gcloud auth login")
        print("   2. gcloud config set project YOUR_PROJECT_ID")
        print("   3. python deploy_gcp.py --list")
        print("   4. python deploy_gcp.py --deploy portfolio_manager")


if __name__ == "__main__":
    main()
