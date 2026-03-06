# 🚀 Streamlit Deployment Guide for Drayvn Agents

This guide explains how to deploy your AI agents to Streamlit Cloud and get demo URLs for the marketplace.

## 📋 Agents Ready for Deployment

| Agent | Folder | Streamlit App | Pattern | Status |
|-------|--------|---------------|---------|--------|
| 🔐 Access Controller | `access_controller_agent/` | `streamlit_app.py` | Hierarchical ADK | ✅ Ready |
| 🎯 Campaign Validator | `campaign_validator_agent/` | `app.py` | Human-in-the-Loop | ✅ Ready |
| 📈 Portfolio Manager | `portfolio_manager/` | `streamlit_app.py` | Sequential Pipeline | ✅ Ready |
| 🔍 PR Code Reviewer | `pr_code_reviewer/` | `streamlit_app.py` | Parallel Swarm | ✅ Ready |
| 🔬 Research Assistant | `research_assistant/` | `streamlit_app.py` | Sequential Pipeline | ✅ Ready |
| 🏦 Loan Underwriter | `FAN out-FAN in/` | `streamlit_app.py` | Fan-Out/Fan-In | ✅ Ready |
| 🛡️ Content Moderator | `social_media_content_moderation/` | `streamlit_app.py` | Parallel Swarm | ✅ Ready |
| 🤖 HelpDesk Bot | `Router Pattern/` | `streamlit_app.py` | Router Pattern | ✅ Ready |
| 📱 Social Media Trends | `social_media_marketing/` | `streamlit_app.py` | Single Agent | ✅ Ready |
| 🐝 Portfolio Swarm | `Swarm Pattern/` | `streamlit_app.py` | Swarm Pattern | ✅ Ready |
| ✉️ Marketing Campaign | `marketing-campaign/` | N/A (Next.js) | Coordinator Pattern | ⚠️ TypeScript |

> **Note:** The Marketing Campaign agent is built with TypeScript/Next.js and has its own web interface. Deploy it separately using Vercel or similar.

## 🛠️ Quick Setup

### 1. Push to GitHub

```bash
cd drayvn_agents
git add .
git commit -m "Add Streamlit demo apps for all agents"
git push origin main
```

### 2. Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"New app"**
3. Select your repository: `your-username/drayvn_agents`
4. Choose branch: `main`
5. Enter the main file path for each agent

### 3. Deploy Each Agent

#### 🔐 Access Controller Agent
- **Main file path:** `access_controller_agent/streamlit_app.py`
- **Expected URL:** `https://access-controller-agent.streamlit.app`

#### 🎯 Campaign Validator Agent
- **Main file path:** `campaign_validator_agent/app.py`
- **Expected URL:** `https://campaign-validator.streamlit.app`

#### 📈 Portfolio Manager
- **Main file path:** `portfolio_manager/streamlit_app.py`
- **Expected URL:** `https://portfolio-manager.streamlit.app`

#### 🔍 PR Code Reviewer
- **Main file path:** `pr_code_reviewer/streamlit_app.py`
- **Expected URL:** `https://pr-code-reviewer.streamlit.app`

#### 🔬 Research Assistant
- **Main file path:** `research_assistant/streamlit_app.py`
- **Expected URL:** `https://research-assistant.streamlit.app`

#### 🏦 Loan Underwriter
- **Main file path:** `FAN out-FAN in/streamlit_app.py`
- **Expected URL:** `https://loan-underwriter.streamlit.app`

#### 🛡️ Content Moderator
- **Main file path:** `social_media_content_moderation/streamlit_app.py`
- **Expected URL:** `https://content-moderator.streamlit.app`

#### 🤖 HelpDesk Bot (Router Pattern)
- **Main file path:** `Router Pattern/streamlit_app.py`
- **Expected URL:** `https://helpdesk-bot.streamlit.app`

#### 📱 Social Media Trends
- **Main file path:** `social_media_marketing/streamlit_app.py`
- **Expected URL:** `https://social-media-trends.streamlit.app`

#### 🐝 Portfolio Swarm
- **Main file path:** `Swarm Pattern/streamlit_app.py`
- **Expected URL:** `https://portfolio-swarm.streamlit.app`

### ⚠️ TypeScript Agent (Deploy Separately)

#### ✉️ Marketing Campaign (Next.js)
This agent uses TypeScript/Next.js. Deploy to **Vercel** instead:
1. Go to [vercel.com](https://vercel.com)
2. Import the `marketing-campaign/` folder
3. Set environment variables
4. Deploy → Get URL like `https://marketing-campaign.vercel.app`

## ⚙️ Environment Variables

Each Streamlit app needs this environment variable in Streamlit Cloud:

```
DRAYVN_API_URL=https://your-drayvn-server.com/api/v1/prediction/FLOW_ID
```

Set this in **Streamlit Cloud Settings** → **Secrets**:

```toml
DRAYVN_API_URL = "https://your-drayvn-server.com/api/v1/prediction/FLOW_ID"
```

## 🔄 Register Demo URLs in Marketplace

After deploying, update your marketplace agents:

### Using the Deploy Script

```bash
# List all agents and their status
python deploy_streamlit_agents.py --list

# Update a single agent
python deploy_streamlit_agents.py --update <agent-marketplace-id> https://your-agent.streamlit.app

# Register all configured agents
python deploy_streamlit_agents.py --register-all
```

### Manual API Update

```bash
curl -X PUT "https://your-drayvn-server.com/api/v1/agent-marketplace/{agentId}" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"demoUrl": "https://your-agent.streamlit.app"}'
```

## 📁 Project Structure

Each agent folder now contains:

```
agent_folder/
├── streamlit_app.py      # Streamlit demo UI
├── .streamlit/
│   └── config.toml       # Streamlit theme config
├── requirements.txt      # Original agent dependencies
└── ... (existing files)
```

## 🎨 Customizing the Demo

Each `streamlit_app.py` is customized for its agent:

- **Access Controller**: Platform selection, example requests
- **Campaign Validator**: Full HITL pipeline (existing app.py)
- **Portfolio Manager**: Interactive risk questionnaire, 8-agent pipeline visualization
- **PR Code Reviewer**: Code diff input, 5-point inspection display
- **Research Assistant**: File upload, analysis modes, web research tabs
- **Loan Underwriter**: Full loan application form, parallel processing visualization
- **Content Moderator**: Text/image/link inputs, parallel analysis display

## 🧪 Testing Locally

```bash
cd agent_folder
pip install streamlit requests python-dotenv
streamlit run streamlit_app.py
```

## 📦 Streamlit Requirements

All demos share common requirements:

```
streamlit>=1.28.0
requests>=2.28.0
python-dotenv>=1.0.0
```

These are already in `streamlit_requirements.txt` at the repo root.

## 🔮 Next Steps

1. ✅ Deploy all agents to Streamlit Cloud
2. ✅ Update `deploy_streamlit_agents.py` with actual Streamlit URLs
3. ✅ Register demo URLs in Drayvn marketplace
4. ✅ Add actual Drayvn API flow IDs to each demo

## 📞 Support

Questions? Check the individual agent README files for specific configuration details.
