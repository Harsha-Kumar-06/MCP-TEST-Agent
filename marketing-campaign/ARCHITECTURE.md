# System Architecture

## 🏗️ Overview

This is a **Multi-Agent Marketing Campaign Automation System** built using the **Coordinator Pattern**. It orchestrates multiple specialized AI agents to plan, create, and execute multi-channel marketing campaigns.

## 📐 Architecture Pattern

### Coordinator Pattern (Multi-Agent System)

```
┌─────────────────────────────────────────────────────────────┐
│                    Campaign Coordinator                      │
│  (Orchestrates all agents and manages campaign execution)   │
└─────────────────┬───────────────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┬──────────────┬──────────────┐
    │             │             │              │              │
    ▼             ▼             ▼              ▼              ▼
┌────────┐  ┌──────────┐  ┌─────────┐  ┌──────────┐  ┌────────────┐
│Audience│  │  Email   │  │   SMS   │  │Instagram │  │ Compliance │
│Segment │  │ Content  │  │ Content │  │ Posting  │  │   Agent    │
│ Agent  │  │  Agent   │  │  Agent  │  │  Agent   │  │            │
└────────┘  └──────────┘  └─────────┘  └──────────┘  └────────────┘
     │            │             │              │              │
     └────────────┴─────────────┴──────────────┴──────────────┘
                            │
                            ▼
                  ┌──────────────────┐
                  │  Sending Agents  │
                  │  - Email Sender  │
                  │  - SMS Sender    │
                  │  - Instagram API │
                  └──────────────────┘
```

## 🎯 System Components

### 1. Frontend Layer (Next.js)

```
pages/
├── index.tsx               # Homepage - Campaign dashboard
├── contacts.tsx            # Contact management
├── campaigns/
│   ├── index.tsx          # Campaign list
│   ├── [id].tsx           # Campaign details (view, resend, delete)
│   ├── create.tsx         # Create new campaign
│   └── edit/[id].tsx      # Edit existing campaign
└── api/                   # Backend API routes
    ├── campaigns/
    │   ├── execute.ts     # Execute campaign with contacts
    │   ├── update.ts      # Update campaign details
    │   ├── resend.ts      # Resend campaign to recipients
    │   └── index.ts       # CRUD operations
    └── contacts/
        ├── index.ts       # Contact CRUD
        ├── lists.ts       # Contact list management
        └── upload-csv.ts  # CSV import
```

### 2. Agent Layer (Multi-Agent System)

```typescript
src/agents/
├── coordinator-agent.ts              # Orchestrates all agents
├── audience-segmentation-agent.ts    # Analyzes & segments audience
├── email-content-agent.ts            # Generates email content
├── sms-content-agent.ts              # Generates SMS content
├── instagram-posting-agent.ts        # Posts to Instagram
├── compliance-agent.ts               # Validates compliance
├── analytics-setup-agent.ts          # Sets up tracking
├── email-sending-agent.ts            # Sends emails via SMTP
└── sms-sending-agent.ts              # Sends SMS via Twilio
```

### 3. Database Layer (File-based JSON)

```
data/
├── campaigns.json       # Campaign records with results
├── contacts.json        # Individual contacts
└── contact-lists.json   # Contact lists with members
```

## 🔄 Data Flow Architecture

### Campaign Execution Flow

```
1. User Input (Frontend)
   │
   ├─→ Campaign Details (product, audience, budget, timeline)
   ├─→ Channel Selection (email, SMS, Instagram)
   ├─→ Recipient Selection (contact list or single contact)
   └─→ Company Info (phone, email, website, social)
   │
   ▼
2. API Layer (/api/campaigns/execute)
   │
   ├─→ Validates input
   ├─→ Fetches contacts from database
   └─→ Calls Coordinator Agent
   │
   ▼
3. Coordinator Agent (orchestrates execution)
   │
   ├─→ Audience Segmentation Agent
   │   └─→ Analyzes demographics, interests, pain points
   │
   ├─→ Content Generation (parallel execution)
   │   ├─→ Email Content Agent
   │   │   ├─→ Generates subject lines (A/B variants)
   │   │   ├─→ Creates HTML email with interactive elements
   │   │   └─→ Generates plain text version
   │   │
   │   └─→ SMS Content Agent
   │       ├─→ Generates concise SMS text (160 chars)
   │       └─→ Adds personalization & CTA
   │
   ├─→ Instagram Posting Agent (if selected)
   │   ├─→ Generates caption with hashtags
   │   └─→ Posts to Instagram via Graph API
   │
   ├─→ Compliance Agent
   │   ├─→ Validates CAN-SPAM compliance
   │   ├─→ Checks opt-in status
   │   └─→ Ensures unsubscribe links
   │
   └─→ Sending Agents (parallel execution)
       │
       ├─→ Email Sending Agent
       │   ├─→ Personalizes content per recipient
       │   ├─→ Sends via Gmail SMTP (Nodemailer)
       │   ├─→ Rate limiting (5 emails/sec)
       │   └─→ Returns success/failure counts
       │
       └─→ SMS Sending Agent
           ├─→ Personalizes SMS per recipient
           ├─→ Sends via Twilio API
           └─→ Returns success/failure counts
   │
   ▼
4. Results Aggregation
   │
   ├─→ Collect results from all agents
   ├─→ Calculate total sent/failed per channel
   └─→ Save to database
   │
   ▼
5. Database Storage
   │
   └─→ Create campaign record with:
       ├─→ Campaign metadata (name, channels, status)
       ├─→ Recipient info (list/single, count)
       ├─→ Results (emails sent/failed, SMS sent/failed, Instagram posts)
       ├─→ Full campaign data (for editing/resending)
       └─→ Recipient data (for resend capability)
   │
   ▼
6. Response to Frontend
   │
   └─→ Returns success status and results
       └─→ Frontend displays results & navigates to campaign list
```

### Campaign Resend Flow

```
1. User clicks "Resend" button
   │
   ▼
2. API: /api/campaigns/resend?id=xxx
   │
   ├─→ Fetches original campaign from database
   ├─→ Retrieves recipient data (contactListId or singleContact)
   ├─→ Fetches current contact list (if list-based)
   │
   ▼
3. Re-executes campaign with original data
   │
   └─→ Follows same execution flow as above
   │
   ▼
4. Creates new campaign record
   │
   └─→ Name: "[Original Name] (Resent)"
   └─→ All other data preserved
```

## 🛠️ Technology Stack

### Frontend
- **Next.js 14.2** - React framework with SSR & API routes
- **TypeScript 5.0** - Type-safe development
- **Tailwind CSS 3.4** - Utility-first styling
- **React 18** - UI library

### Backend
- **Node.js** - Runtime environment
- **Next.js API Routes** - RESTful API endpoints
- **TypeScript** - Type-safe backend

### Integrations
- **Nodemailer 6.9** - Email sending via Gmail SMTP
- **Twilio 4.19** - SMS sending API
- **Facebook Graph API v18** - Instagram posting
- **Formidable 3.5** - CSV file parsing

### Database
- **File-based JSON** - Simple, no setup required
- Easily upgradable to PostgreSQL/MongoDB

## 📊 Database Schema

### Campaign Record
```typescript
{
  id: string;                    // Unique campaign ID
  campaignName: string;          // Campaign name
  channels: string[];            // ['email', 'sms', 'instagram']
  status: 'completed' | 'failed' | 'pending';
  recipientType: 'list' | 'single';
  recipientCount: number;
  recipientInfo: string;         // List name or contact email
  executedAt: Date;
  results: {
    emailsSent?: number;
    emailsFailed?: number;
    smsSent?: number;
    smsFailed?: number;
    instagramPosts?: number;
  };
  campaignData: CampaignRequest; // Full campaign request
  recipientData?: {              // For resend capability
    contactListId?: string;
    singleContact?: Contact;
  };
}
```

### Contact Record
```typescript
{
  id: string;
  email: string;
  phone?: string;
  firstName: string;
  lastName: string;
  company?: string;
  tags?: string[];
  customFields?: Record<string, any>;
  optInEmail: boolean;
  optInSMS: boolean;
  createdAt: Date;
}
```

### Contact List Record
```typescript
{
  id: string;
  name: string;
  description?: string;
  contacts: Contact[];
  createdAt: Date;
  updatedAt: Date;
}
```

## 🔐 Security & Configuration

### Environment Variables (.env)
```bash
# Email Configuration (Gmail SMTP)
GMAIL_USER=your.email@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
FROM_NAME=Campaign Manager

# Company Contact Info (defaults for emails)
COMPANY_PHONE=+1-555-0100
COMPANY_WEBSITE=https://yourcompany.com
BOOKING_LINK=https://calendly.com/yourcompany/demo

# SMS Configuration (Twilio)
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=xxxxx
TWILIO_PHONE_NUMBER=+1234567890

# Instagram Configuration (Facebook Graph API)
INSTAGRAM_ACCESS_TOKEN=xxxxx
INSTAGRAM_ACCOUNT_ID=xxxxx
```

## 🚀 API Endpoints

### Campaign Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/campaigns/execute` | Execute campaign with contacts |
| GET | `/api/campaigns` | List all campaigns |
| PUT | `/api/campaigns/update?id=xxx` | Update campaign details |
| POST | `/api/campaigns/resend?id=xxx` | Resend campaign to same recipients |
| DELETE | `/api/campaigns?id=xxx` | Delete campaign |

### Contact Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/contacts` | List all contacts |
| POST | `/api/contacts` | Create new contact |
| GET | `/api/contacts/lists` | List all contact lists |
| POST | `/api/contacts/lists` | Create new contact list |
| POST | `/api/contacts/upload-csv` | Import contacts from CSV |

## 🎨 Frontend Architecture

### Page Components
```
┌──────────────────────────────────────────────────────────┐
│                      Navigation Bar                       │
│  Home | Campaigns | New Campaign | Contacts              │
└──────────────────────────────────────────────────────────┘
         │
         ├─→ Homepage (index.tsx)
         │   ├─→ Campaign statistics
         │   ├─→ Recent campaigns list
         │   └─→ Quick actions
         │
         ├─→ Campaign List (campaigns/index.tsx)
         │   ├─→ All campaigns table
         │   ├─→ Filter by status/channel
         │   └─→ Actions: View, Edit, Delete
         │
         ├─→ Campaign Detail (campaigns/[id].tsx)
         │   ├─→ Campaign info & results
         │   ├─→ Actions: Resend, Edit, Delete
         │   └─→ Full campaign data JSON
         │
         ├─→ Create Campaign (campaigns/create.tsx)
         │   ├─→ Multi-step form
         │   ├─→ Channel selection (Email/SMS/Instagram)
         │   ├─→ Recipient mode (List/Single)
         │   ├─→ Product details
         │   ├─→ Target audience
         │   ├─→ Timeline & budget
         │   └─→ Company contact info
         │
         ├─→ Edit Campaign (campaigns/edit/[id].tsx)
         │   ├─→ Pre-filled form with campaign data
         │   ├─→ Optional resend after edit
         │   └─→ Update campaign
         │
         └─→ Contacts (contacts.tsx)
             ├─→ Contact list table
             ├─→ CSV import
             ├─→ Create contact lists
             └─→ Launch campaigns from lists
```

## 🔌 Channel Integration Architecture

### Email Channel (Gmail SMTP)
```
User Input → Email Content Agent → Email Sending Agent
                                          │
                                          ├─→ Nodemailer
                                          │   └─→ Gmail SMTP
                                          │       ├─→ Host: smtp.gmail.com
                                          │       ├─→ Port: 587 (TLS)
                                          │       └─→ Auth: App Password
                                          │
                                          ├─→ Personalization
                                          │   ├─→ {{firstName}} replacement
                                          │   ├─→ {{lastName}} replacement
                                          │   └─→ Custom fields
                                          │
                                          ├─→ Interactive Elements
                                          │   ├─→ tel: links (click to call)
                                          │   ├─→ mailto: links
                                          │   ├─→ Booking buttons
                                          │   ├─→ Social media icons
                                          │   └─→ Reply-to header
                                          │
                                          └─→ Rate Limiting (5/sec)
```

### SMS Channel (Twilio API)
```
User Input → SMS Content Agent → SMS Sending Agent
                                       │
                                       ├─→ Twilio Client
                                       │   └─→ REST API
                                       │       ├─→ Endpoint: api.twilio.com
                                       │       ├─→ Auth: SID + Token
                                       │       └─→ From: Twilio number
                                       │
                                       ├─→ Character Limit (160)
                                       ├─→ Personalization
                                       └─→ Opt-in Validation
```

### Instagram Channel (Facebook Graph API)
```
User Input → Instagram Posting Agent
                    │
                    ├─→ Generate Caption
                    │   ├─→ Product description
                    │   ├─→ Features list
                    │   ├─→ Hashtags (10 max)
                    │   └─→ Call-to-action
                    │
                    └─→ Facebook Graph API
                        ├─→ Step 1: Create Media Container
                        │   POST /v18.0/{account}/media
                        │   └─→ Returns: creation_id
                        │
                        └─→ Step 2: Publish Post
                            POST /v18.0/{account}/media_publish
                            └─→ Returns: media_id
                            └─→ URL: instagram.com/p/{shortcode}
```

## 🧪 Agent Communication Protocol

### Agent Result Interface
```typescript
interface AgentResult {
  success: boolean;
  agentType: string;
  data?: any;
  error?: string;
  timestamp: Date;
}
```

### Agent Execution Flow
1. **Coordinator** sends request to agent
2. **Agent** processes request
3. **Agent** returns standardized result
4. **Coordinator** aggregates results
5. **Coordinator** decides next actions based on results

## 📈 Scalability Considerations

### Current Implementation
- File-based JSON database (suitable for small-scale)
- Synchronous campaign execution
- Single server instance

### Future Scalability Options
1. **Database Migration**
   - Replace JSON files with PostgreSQL/MongoDB
   - Add indexing for faster queries
   - Support millions of contacts

2. **Async Processing**
   - Queue system (Bull/BullMQ)
   - Background job processing
   - Parallel campaign execution

3. **Horizontal Scaling**
   - Load balancer
   - Multiple Next.js instances
   - Redis session storage

4. **AI Enhancement**
   - Integrate OpenAI API for content generation
   - Use Claude/GPT-4 for personalization
   - A/B testing optimization

## 🔍 Error Handling

### Campaign Execution Errors
- Agent failures logged but don't stop execution
- Partial success supported (e.g., email succeeds, SMS fails)
- Failed campaigns saved with status='failed'

### API Error Responses
```typescript
{
  success: false,
  error: "Error message",
  code?: "ERROR_CODE"
}
```

## 🎯 Design Principles

1. **Separation of Concerns**
   - Each agent has single responsibility
   - UI separated from business logic
   - Database layer abstracted

2. **Modularity**
   - Agents are pluggable
   - Easy to add new channels
   - Swappable database implementations

3. **Type Safety**
   - Full TypeScript coverage
   - Interface-driven development
   - Compile-time error detection

4. **User-Centric Design**
   - Simple, intuitive UI
   - Clear feedback on actions
   - Error messages explain next steps

## 📝 Key Features

### Multi-Channel Support
- ✉️ Email (Gmail SMTP - free, unlimited within limits)
- 📱 SMS (Twilio API - paid, requires A2P 10DLC)
- 📸 Instagram (Facebook Graph API - free, 200 posts/day)

### Campaign Management
- Create campaigns with detailed targeting
- Edit existing campaigns
- Resend campaigns to same recipients
- Delete campaigns
- View detailed results

### Contact Management
- Import contacts via CSV
- Create contact lists
- Single contact campaigns
- Opt-in/opt-out tracking

### Personalization
- Dynamic content insertion ({{firstName}}, etc.)
- Per-campaign contact info override
- A/B testing variants
- Brand voice customization

### Interactive Elements
- Click-to-call phone links
- Email reply-to functionality
- Booking calendar integration
- Social media links
- Website CTAs

## 🚦 Getting Started

1. **Install dependencies**: `npm install`
2. **Configure .env**: Add Gmail, Twilio, Instagram credentials
3. **Start server**: `npm run dev`
4. **Access UI**: http://localhost:3000
5. **Create campaign**: Import contacts → Create campaign → Execute

## 📚 Documentation Files

- `README.md` - Project overview & setup
- `SETUP-GUIDE.md` - Detailed setup instructions
- `INSTAGRAM-QUICK-SETUP.md` - 10-minute Instagram setup
- `INSTAGRAM-SETUP.md` - Full Instagram integration guide
- `ARCHITECTURE.md` - This file (system architecture)

---

**Built with:** Next.js, TypeScript, Tailwind CSS, Nodemailer, Twilio, Facebook Graph API
**Pattern:** Multi-Agent Coordinator
**License:** MIT
