# Multi-Agent Coordinator Pattern
## Marketing Campaign Automation (Email & SMS)

A TypeScript implementation of the multi-agent coordinator pattern for automating marketing campaigns with dynamic routing and specialized agents.

## 🎯 Overview

This system uses a **central coordinator agent** that intelligently analyzes campaign requests, breaks them down into sub-tasks, and dynamically routes each task to specialized agents. Each agent is an expert in a specific domain (email content, SMS content, audience segmentation, compliance, analytics).

## 🏗️ Architecture

```
                    ┌─────────────────────┐
                    │  Campaign Request   │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Coordinator Agent  │
                    │  (Genkit/Gemini AI) │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
┌───────▼────────┐   ┌────────▼────────┐   ┌────────▼────────┐
│ Email Agent    │   │  SMS Agent      │   │ Instagram Agent │
│ (Content)      │   │  (Content)      │   │ (Posting)       │
└────────────────┘   └─────────────────┘   └─────────────────┘
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
┌───────▼────────┐   ┌────────▼────────┐   ┌────────▼────────┐
│ Audience Agent │   │ Compliance Agent│   │ Analytics Agent │
│ (Segmentation) │   │ (Validation)    │   │ (Tracking)      │
└────────────────┘   └─────────────────┘   └─────────────────┘
```

## 🚀 Features

- **Dynamic Routing**: AI-powered coordinator determines which agents to invoke based on campaign requirements
- **Google ADK Integration**: Powered by Genkit with Gemini 2.5 Flash (FREE tier available)
- **Specialized Agents**: Each agent focuses on a specific task
  - 👥 Audience Segmentation Agent
  - ✉️ Email Content Agent (with A/B testing)
  - 📱 SMS Content Agent (with character optimization)
  - 📸 Instagram Posting Agent (automatic posting)
  - ⚖️ Compliance Agent (CAN-SPAM, TCPA, GDPR)
  - 📊 Analytics Setup Agent (UTM tracking, KPIs)
- **Multi-Channel Support**: Email, SMS, and Instagram in coordinated campaigns
- **Dependency Management**: Tasks execute in the correct order based on dependencies
- **Compliance Checking**: Automatic regulatory compliance validation
- **A/B Testing**: Built-in variant generation for optimization
- **Web UI**: Full-featured Next.js dashboard for campaign management

## 📦 Installation

```bash
# Install dependencies
npm install

# Copy environment file (Windows)
copy .env.example .env

# Copy environment file (Mac/Linux)
cp .env.example .env

# Add your API keys to .env (see Configuration section)
```

## 🎮 Usage

### Basic Example (Email + SMS Campaign)

```typescript
import { MarketingCampaignOrchestrator } from './src/index';
import { CampaignRequest } from './src/types/campaign';

const campaignRequest: CampaignRequest = {
  campaignId: 'camp-2026-001',
  campaignName: 'Product Launch Campaign',
  channels: ['email', 'sms'],
  
  product: {
    name: 'TaskFlow Pro',
    description: 'AI-powered project management tool',
    features: [
      'AI task prioritization',
      'Real-time collaboration',
      'Automated workflows',
    ],
    pricing: '$29/month',
  },
  
  targetAudience: {
    demographics: 'Software teams, 10-100 employees',
    interests: ['Project management', 'Productivity'],
    painPoints: ['Missed deadlines', 'Poor coordination'],
  },
  
  budget: 15000,
  timeline: {
    startDate: '2026-02-15',
    endDate: '2026-03-15',
  },
  goals: ['Generate 1,000 leads', 'Achieve 500 signups'],
  brandVoice: 'friendly',
};

const orchestrator = new MarketingCampaignOrchestrator();
await orchestrator.executeCampaign(campaignRequest);
```

### Run Examples

```bash
# Run the email + SMS campaign example (terminal)
npm run example

# Or run individual examples
npx ts-node src/examples/email-only-campaign.ts
npx ts-node src/examples/sms-only-campaign.ts

# Run with Genkit Developer UI (recommended for testing)
npm install -g genkit
genkit start -- npx tsx src/index.ts
# Then open http://localhost:4000 in your browser
```

### Run the Web UI

```bash
# Start the Next.js development server
npm run dev
# Then open http://localhost:3000 in your browser
```

## 📁 Project Structure

```
src/
├── agents/
│   ├── coordinator-agent.ts           # Main coordinator (brain)
│   ├── audience-segmentation-agent.ts # Audience analysis
│   ├── email-content-agent.ts         # Email generation
│   ├── email-sending-agent.ts         # Email delivery (Gmail SMTP)
│   ├── sms-content-agent.ts           # SMS generation
│   ├── sms-sending-agent.ts           # SMS delivery (Twilio/Vonage/Plivo/Textbelt)
│   ├── instagram-posting-agent.ts     # Instagram posting (Graph API)
│   ├── compliance-agent.ts            # Legal compliance
│   └── analytics-setup-agent.ts       # Tracking setup
├── config/
│   ├── google-adk-config.ts           # Google ADK/Genkit configuration
│   ├── llm-config.ts                  # AI model configuration
│   └── init.ts                        # Service initialization
├── database/
│   ├── campaign-database.ts           # Campaign storage
│   ├── contact-database.ts            # Contact management
│   └── tracking-database.ts           # Analytics tracking
├── scheduler/
│   └── campaign-scheduler.ts          # Scheduled campaign execution
├── types/
│   ├── campaign.ts                    # TypeScript interfaces
│   └── database.ts                    # Database types
├── examples/
│   ├── email-sms-campaign.ts          # Combined example
│   ├── email-only-campaign.ts         # Email-only example
│   └── sms-only-campaign.ts           # SMS-only example
└── index.ts                           # Main orchestrator

pages/                                 # Next.js frontend
├── index.tsx                          # Dashboard
├── contacts.tsx                       # Contact management
├── campaigns/
│   ├── index.tsx                      # Campaign list
│   ├── create.tsx                     # Create campaign
│   ├── [id].tsx                       # Campaign details
│   ├── templates.tsx                  # Template library
│   └── edit/[id].tsx                  # Edit campaign
└── api/                               # API routes
    ├── campaigns/                     # Campaign APIs
    ├── contacts/                      # Contact APIs
    └── track/                         # Tracking APIs
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with your API keys:

```env
# Google ADK (Genkit/Gemini) - RECOMMENDED (FREE TIER AVAILABLE)
# Get API key from: https://aistudio.google.com/apikey
GOOGLE_GENAI_API_KEY=your_google_api_key_here

# Model Selection (Latest as of Feb 2026):
# - 'flash' = gemini-2.5-flash (RECOMMENDED - best price-performance, FREE)
# - 'lite'  = gemini-2.5-flash-lite (fastest, FREE)
# - 'pro'   = gemini-2.5-pro (advanced reasoning)
GOOGLE_MODEL=flash

# LLM Provider: 'auto' (recommended), 'google', or 'openai'
LLM_PROVIDER=auto

# Optional: OpenAI (fallback)
OPENAI_API_KEY=your_openai_key_here

# Gmail SMTP (for sending emails)
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-16-char-app-password
FROM_NAME=Your Company Name

# SMS Provider (choose one: twilio | vonage | plivo | textbelt)
SMS_PROVIDER=textbelt

# Textbelt (FREE - no account needed, 1 SMS/day)
TEXTBELT_API_KEY=textbelt

# OR Twilio (optional)
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+15551234567

# OR Vonage (optional)
VONAGE_API_KEY=your_key
VONAGE_API_SECRET=your_secret
VONAGE_FROM_NUMBER=+15551234567

# OR Plivo (optional)
PLIVO_AUTH_ID=your_auth_id
PLIVO_AUTH_TOKEN=your_token
PLIVO_FROM_NUMBER=+15551234567

# Instagram (for posting - optional)
INSTAGRAM_ACCESS_TOKEN=EAA...
INSTAGRAM_ACCOUNT_ID=17841234567890123
```

### LLM Configuration

The system uses Google ADK (Genkit) with Gemini 2.5 Flash by default. Edit `src/config/llm-config.ts` to customize:

```typescript
export const LLMConfig = {
  provider: 'auto',           // 'auto', 'google', or 'openai'
  googleModel: 'flash',       // 'flash', 'lite', or 'pro'
  temperature: 0.7,
  maxTokens: 2000,
};
```

## 🎯 Use Cases

Perfect for:
- **Multi-channel marketing campaigns** (Email + SMS)
- **Product launches** with coordinated messaging
- **Time-sensitive promotions** (flash sales, limited offers)
- **Lead generation campaigns** with nurture sequences
- **Customer engagement** and retention campaigns

## ✅ Compliance

The system automatically checks for:
- **CAN-SPAM Act** (Email marketing regulations)
- **TCPA** (SMS/text message regulations)
- **GDPR** (European data protection)
- **CCPA** (California privacy laws)

## 📊 Analytics & Tracking

Automatic setup of:
- UTM parameters for all links
- Conversion goal tracking
- KPI definitions
- A/B testing variants
- Dashboard configuration

## 🚀 Extending the System

### Add a New Agent

1. Create agent file in `src/agents/`:
```typescript
export class NewAgent {
  async execute(request: CampaignRequest): Promise<AgentResult> {
    // Your agent logic
  }
}
```

2. Add to coordinator routing in `coordinator-agent.ts`:
```typescript
case 'new-agent':
  const { NewAgent } = await import('./new-agent');
  result = await new NewAgent().execute(request);
  break;
```

3. Update agent types in `src/types/campaign.ts`:
```typescript
export type AgentType = ... | 'new-agent';
```

## 📝 Example Output

```
============================================================
🚀 MULTI-AGENT COORDINATOR SYSTEM
   Marketing Campaign Automation
============================================================

Campaign: Q1 Product Launch - Email & SMS
ID: camp-2026-q1-001
Channels: EMAIL, SMS
Budget: $15,000
Timeline: 2026-02-15 to 2026-03-15
============================================================

🎯 COORDINATOR AGENT: Starting campaign coordination...
Campaign: Q1 Product Launch - Email & SMS
Channels: email, sms
────────────────────────────────────────────────────────────

📋 COORDINATOR: Analyzing campaign requirements...
📊 COORDINATOR: Identified 5 sub-tasks:
  • [HIGH] audience-segmentation: Analyze and segment target audience
  • [HIGH] email-content: Generate email marketing content
  • [HIGH] sms-content: Generate SMS marketing content
  • [HIGH] compliance: Review campaign for legal compliance
  • [MEDIUM] analytics-setup: Configure tracking and analytics

👥 AUDIENCE SEGMENTATION AGENT: Analyzing target audience...
✅ Created 3 audience segments:
   • Primary Target (1500 estimated reach)
   • High Intent Leads (450 estimated reach)
   • Email Nurture Segment (750 estimated reach)

✉️  EMAIL CONTENT AGENT: Generating email content...
✅ Email content generated:
   • Subject: We think you'll love TaskFlow Pro!
   • CTA: Start Your Free Trial
   • Variants: 2 A/B test options

📱 SMS CONTENT AGENT: Generating SMS content...
✅ SMS content generated:
   • Message: Hey! 👋 Check out TaskFlow Pro - AI-powered task...
   • Length: 124 chars (1 SMS)
   • Variants: 2 A/B test options

⚖️  COMPLIANCE AGENT: Reviewing campaign compliance...
✅ Compliance check passed:
   • Issues: 3 (0 critical)
   • Recommendations: 15

📊 ANALYTICS SETUP AGENT: Configuring tracking...
✅ Analytics configured:
   • UTM Campaign: camp-2026-q1-001
   • UTM Source: marketing-automation
   • UTM Medium: multi-channel
   • Conversion Goals: 4 defined
   • Tracking URLs: 7 generated

✅ Campaign setup complete!
```

## 🤝 Contributing

Feel free to extend this system with additional agents or features!

## 📄 License

MIT
