# Unified Deployment - All Agents in One Cloud Run

This setup deploys **all 10 agents in a single Cloud Run service** with route-based access.

## Architecture

```
                    ┌─────────────────────────────────────────┐
                    │         Cloud Run Service               │
                    │         (drayvn-agents-demo)            │
                    │                                         │
   Internet ───────►│  nginx (port 8080)                      │
                    │    │                                    │
                    │    ├─► /                → Landing Page  │
                    │    ├─► /access-controller → Port 8502   │
                    │    ├─► /portfolio-manager → Port 8503   │
                    │    ├─► /campaign-validator→ Port 8504   │
                    │    ├─► /pr-code-reviewer → Port 8505    │
                    │    ├─► /research-assistant→ Port 8506   │
                    │    ├─► /loan-underwriter → Port 8507    │
                    │    ├─► /content-moderator→ Port 8508    │
                    │    ├─► /helpdesk-bot    → Port 8509     │
                    │    ├─► /social-media-trends→ Port 8510  │
                    │    └─► /portfolio-swarm → Port 8511     │
                    │                                         │
                    │  supervisord manages all processes      │
                    └─────────────────────────────────────────┘
```

## Files

```
drayvn_agents/
├── Dockerfile.unified          # Main Dockerfile for unified deployment
├── deploy_unified.bat          # One-click deployment script
└── unified_deployment/
    ├── nginx.conf              # Nginx reverse proxy config (routes → ports)
    ├── supervisord.conf        # Process manager (starts 11 Streamlit apps)
    ├── landing_page.py         # Home page showing all agents
    └── requirements.txt        # Base Python dependencies
```

## Deployment

### Prerequisites
1. Google Cloud SDK installed
2. Logged in: `gcloud auth login`
3. Project with billing enabled

### Deploy

```cmd
# Edit deploy_unified.bat to set:
#   PROJECT_ID=your-project-id
#   GOOGLE_API_KEY=your-api-key

# Then run:
deploy_unified.bat
```

### Result
One URL, all agents:
```
https://drayvn-agents-demo-xxxxx.us-central1.run.app/
https://drayvn-agents-demo-xxxxx.us-central1.run.app/access-controller
https://drayvn-agents-demo-xxxxx.us-central1.run.app/portfolio-manager
https://drayvn-agents-demo-xxxxx.us-central1.run.app/campaign-validator
... etc
```

## Routes

| Route | Agent | Pattern |
|-------|-------|---------|
| `/` | Landing Page | - |
| `/access-controller` | Access Controller Agent | Hierarchical ADK |
| `/portfolio-manager` | Portfolio Manager | Sequential Pipeline |
| `/campaign-validator` | Campaign Validator | Human-in-the-Loop |
| `/pr-code-reviewer` | PR Code Reviewer | Parallel Swarm |
| `/research-assistant` | Research Assistant | Sequential Pipeline |
| `/loan-underwriter` | Loan Underwriter | Fan-Out/Fan-In |
| `/content-moderator` | Content Moderator | Parallel Swarm |
| `/helpdesk-bot` | HelpDesk Bot | Router Pattern |
| `/social-media-trends` | Social Media Trends | Single Agent |
| `/portfolio-swarm` | Portfolio Swarm | Swarm Pattern |

## Resource Requirements

The unified deployment needs more resources than individual deployments:

- **Memory:** 4Gi (runs 11 Streamlit apps + nginx)
- **CPU:** 2 vCPUs
- **Min instances:** 0 (scales to zero when idle)
- **Max instances:** 3 (handles traffic spikes)

## Cost Comparison

| Approach | Services | Cold Start | Monthly Cost (estimate) |
|----------|----------|------------|------------------------|
| Separate (10 services) | 10 | Each ~10s | ~$30-50 |
| Unified (1 service) | 1 | ~30s | ~$15-25 |

## Troubleshooting

### Check logs
```cmd
gcloud run services logs read drayvn-agents-demo --region=us-central1
```

### Check service status
```cmd
gcloud run services describe drayvn-agents-demo --region=us-central1
```

### Delete service
```cmd
gcloud run services delete drayvn-agents-demo --region=us-central1
```
