# 🚀 Full Implementation Complete!

## What's Included

### ✅ AI Integration (Google ADK/Genkit)
- **Gemini 2.5 Flash** - Primary AI model (FREE tier available)
- **Genkit Developer UI** - Test agents interactively at localhost:4000
- **Auto-fallback** - Falls back to OpenAI if configured

### ✅ Backend (Node.js/TypeScript)
- **Multi-agent coordinator system** with dynamic routing
- **6 specialized agents**: Audience Segmentation, Email Content, SMS Content, Instagram Posting, Compliance, Analytics
- **3 sending agents**: Email (Gmail SMTP), SMS (Twilio/Vonage/Plivo/Textbelt), Instagram (Graph API)
- **Contact database** (file-based, easily replaceable with PostgreSQL/MongoDB)
- **CSV import** functionality

### ✅ Frontend (Next.js/React)
- **Campaign creation UI** with full form
- **Document upload** - Auto-fill from PDF/DOCX/TXT
- **Contact management** page
- **CSV upload** interface
- **Template library** - Save and reuse campaigns
- **Dashboard** homepage

### ✅ Integration
- **Google ADK (Genkit)** with Gemini 2.5 Flash for AI content generation
- **Gmail SMTP** for email sending (using Nodemailer)
- **Twilio** for SMS sending (free trial available)
- **Instagram Graph API** for automatic posting
- **API routes** for all operations

---

## 🔧 Setup Instructions

### 1. Install Dependencies

```bash
cd marketing-campaign
npm install
```

### 2. Configure Google ADK (Recommended - FREE)

The system uses Google ADK (Genkit) with Gemini 2.5 Flash as the primary AI provider.

#### Step 1: Get Google API Key
1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Create or select a project
3. Generate an API key
4. Copy the key

#### Step 2: Add to `.env` file
```env
GOOGLE_GENAI_API_KEY=your_api_key_here
GOOGLE_MODEL=flash
LLM_PROVIDER=auto
```

### 3. Configure Gmail SMTP

#### Step 1: Enable 2-Factor Authentication
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Step Verification

#### Step 2: Create App Password
1. Go to [App Passwords](https://myaccount.google.com/apppasswords)
2. Select "Mail" and "Windows Computer"
3. Click "Generate"
4. Copy the 16-character password

### 3. Configure SMS Provider (Optional)

Choose one provider. **Textbelt is recommended for testing** (no account needed).

#### Option A: Textbelt (Easiest - NO SIGNUP REQUIRED)
- Free tier: 1 SMS/day (no account needed)
- Paid tier: $0.05/SMS - https://textbelt.com/

```env
SMS_PROVIDER=textbelt
TEXTBELT_API_KEY=textbelt
```

#### Option B: Vonage (Good International Coverage)
1. Sign up: https://dashboard.nexmo.com/sign-up
2. Get €2 free credit
3. Copy API Key and Secret from dashboard

```env
SMS_PROVIDER=vonage
VONAGE_API_KEY=your_key
VONAGE_API_SECRET=your_secret
VONAGE_FROM_NUMBER=your_number
```

#### Option C: Plivo (Best Pricing)
1. Sign up: https://console.plivo.com/accounts/register/
2. Get $0.50 free credit

```env
SMS_PROVIDER=plivo
PLIVO_AUTH_ID=your_auth_id
PLIVO_AUTH_TOKEN=your_token
PLIVO_FROM_NUMBER=your_number
```

#### Option D: Twilio
1. Sign up: https://www.twilio.com/try-twilio
2. Get $15 free credit (~500 SMS)

```env
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=ACxxxx
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+15551234567
```

### 5. Create .env File

```bash
# Copy the example file (Windows)
copy .env.example .env

# Copy the example file (Mac/Linux)
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Google ADK (Genkit/Gemini) - RECOMMENDED (FREE)
GOOGLE_GENAI_API_KEY=your_google_api_key_here
GOOGLE_MODEL=flash
LLM_PROVIDER=auto

# Gmail SMTP
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-16-char-app-password
FROM_NAME=Your Company Name

# SMS Provider (choose one: textbelt, vonage, plivo, twilio)
SMS_PROVIDER=textbelt
TEXTBELT_API_KEY=textbelt

# OR Twilio
# SMS_PROVIDER=twilio
# TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# TWILIO_AUTH_TOKEN=your_auth_token_here
# TWILIO_PHONE_NUMBER=+15551234567

# OR Vonage
# SMS_PROVIDER=vonage
# VONAGE_API_KEY=your_key
# VONAGE_API_SECRET=your_secret
# VONAGE_FROM_NUMBER=your_number

# OR Plivo
# SMS_PROVIDER=plivo
# PLIVO_AUTH_ID=your_auth_id
# PLIVO_AUTH_TOKEN=your_token
# PLIVO_FROM_NUMBER=your_number

# Instagram (for automatic posting - supports Image/Video/Carousel/Story)
# See INSTAGRAM-QUICK-SETUP.md for detailed instructions
# Token MUST start with "EAA..." (use Facebook Login method, NOT Instagram Login)
INSTAGRAM_ACCESS_TOKEN=EAA...
INSTAGRAM_ACCOUNT_ID=17841234567890123
```

### 6. Configure Instagram (Optional)

Follow the detailed guide in `INSTAGRAM-QUICK-SETUP.md` or:

1. Create Facebook App at https://developers.facebook.com/apps/create/
2. Select "Other" → "Business" → Choose "Instagram" use case
3. Add "Facebook Login for Business" product
4. Get token from Graph API Explorer (must start with `EAA...`)
5. Get Instagram Business Account ID (format: `17841xxxxxxxxxx`)
6. Add to `.env` file

**Supported Post Types:**
- 📷 Image posts
- 🎬 Video/Reels
- 🎠 Carousel (2-10 images)
- 📱 Stories

### 7. Run the Application

```bash
# Start Next.js development server (Web UI)
npm run dev

# Run example agent (terminal)
npm run example

# Run with Genkit Developer UI
npm install -g genkit
genkit start -- npx tsx src/index.ts
```

Open:
- Web UI: [http://localhost:3000](http://localhost:3000)
- Genkit UI: [http://localhost:4000](http://localhost:4000) (if using genkit start)

---

## 📋 How to Use

### Option 1: Upload CSV
1. Go to **Contacts** page
2. Click "📤 Upload CSV"
3. Select `sample-contacts.csv` (or your own)
4. Give it a name (e.g., "Q1 Leads")
5. Click "Upload"
6. Duplicates (same email/phone) are automatically skipped

**Contact List Features:**
- Paginated display (50 per page)
- Quick jump navigation (Page 1: #1-50, Page 2: #51-100, etc.)
- Delete list also removes associated contacts

### Option 2: API Request (Backend)
Create a file `test-campaign.ts`:

```typescript
import { contactDB } from './src/database/contact-database';
import { MarketingCampaignOrchestrator } from './src/index';

async function runTest() {
  // Create test contacts
  const contact1 = await contactDB.createContact({
    email: 'test@example.com',
    phone: '+15551234567',
    firstName: 'Test',
    lastName: 'User',
    company: 'Test Co',
    tags: ['test'],
    optInEmail: true,
    optInSMS: true,
  });

  // Create list
  const list = await contactDB.createList({
    name: 'Test List',
    description: 'Testing campaign',
    contacts: [contact1],
  });

  // Execute campaign
  const orchestrator = new MarketingCampaignOrchestrator();
  await orchestrator.executeCampaignWithContacts(
    {
      campaignId: 'test-001',
      campaignName: 'Test Campaign',
      channels: ['email', 'sms'],
      product: {
        name: 'Test Product',
        description: 'Testing the system',
        features: ['Feature 1', 'Feature 2'],
      },
      targetAudience: {
        demographics: 'Everyone',
        interests: ['Tech'],
        painPoints: ['None'],
      },
      budget: 1000,
      timeline: {
        startDate: '2026-02-01',
        endDate: '2026-02-28',
      },
      goals: ['Test the system'],
      brandVoice: 'friendly',
    },
    list.contacts
  );
}

runTest();
```

Run: `npx ts-node test-campaign.ts`

### Option 3: Web UI
1. **Upload contacts** (Contacts page)
2. **Create campaign** (New Campaign page)
3. Fill in the form
4. Select your contact list
5. Click "🚀 Execute Campaign"

---

## 📊 How It Works

### Flow Diagram

```
User Creates Campaign (UI/API)
         ↓
Coordinator Agent Analyzes
         ↓
   ┌─────┴─────┐
   ↓           ↓
Content    Audience
Agents     Agent
   ↓           ↓
   └─────┬─────┘
         ↓
   Compliance Check
         ↓
   Analytics Setup
         ↓
   ┌─────┴─────┐
   ↓           ↓
Email       SMS
Sending     Sending
(Gmail)  (Multi-Provider)
   ↓           ↓
Recipients receive messages
```

### What Gets Sent

**Emails:**
- Personalized with `{{firstName}}`, `{{lastName}}`, etc.
- HTML + Plain text versions
- Unsubscribe links
- Tracking URLs

**SMS:**
- Max 160 characters
- Personalized
- Short URLs
- Opt-out instructions

---

## 🎯 Features

| Feature | Status | Notes |
|---------|--------|-------|
| Google ADK (Genkit) | ✅ | Gemini 2.5 Flash - FREE tier |
| Email Sending | ✅ | Gmail SMTP via Nodemailer |
| SMS Sending | ✅ | Twilio (free trial) |
| Instagram Posting | ✅ | Facebook Graph API - FREE |
| CSV Upload | ✅ | Frontend + API |
| Contact Management | ✅ | File-based DB |
| Campaign UI | ✅ | Next.js forms |
| Compliance Checking | ✅ | CAN-SPAM, TCPA, GDPR |
| A/B Testing | ✅ | Variants generated |
| Analytics Tracking | ✅ | UTM parameters |
| Personalization | ✅ | Merge tags |
| Rate Limiting | ✅ | Prevents spam flags |
| Genkit Dev UI | ✅ | Test agents at localhost:4000 |

---

## 📂 File Structure

```
├── pages/
│   ├── index.tsx                    # Homepage/Dashboard
│   ├── contacts.tsx                 # Contact management
│   ├── campaigns/
│   │   ├── index.tsx                # Campaign list
│   │   ├── create.tsx               # Campaign form
│   │   ├── templates.tsx            # Template library
│   │   └── [id].tsx                 # Campaign details
│   └── api/
│       ├── contacts/                # Contact APIs
│       ├── campaigns/               # Campaign APIs
│       └── track/                   # Tracking APIs
├── src/
│   ├── agents/
│   │   ├── coordinator-agent.ts     # Main coordinator
│   │   ├── email-sending-agent.ts   # Gmail SMTP
│   │   ├── sms-sending-agent.ts     # Twilio SMS
│   │   ├── instagram-posting-agent.ts # Instagram Graph API
│   │   ├── email-content-agent.ts   # Email content generation
│   │   ├── sms-content-agent.ts     # SMS content generation
│   │   ├── audience-segmentation-agent.ts # Audience analysis
│   │   ├── compliance-agent.ts      # Legal checks
│   │   └── analytics-setup-agent.ts # Tracking setup
│   ├── config/
│   │   ├── google-adk-config.ts     # Google ADK/Genkit setup
│   │   ├── llm-config.ts            # LLM configuration
│   │   └── init.ts                  # Service initialization
│   ├── database/
│   │   ├── campaign-database.ts     # Campaign storage
│   │   ├── contact-database.ts      # Contact storage
│   │   └── tracking-database.ts     # Analytics tracking
│   ├── scheduler/
│   │   └── campaign-scheduler.ts    # Scheduled execution
│   ├── types/
│   │   ├── campaign.ts              # Campaign types
│   │   └── database.ts              # Database types
│   └── index.ts                     # Main orchestrator
├── data/                            # Auto-created for contacts
├── sample-contacts.csv              # Example CSV
├── sample-campaign-*.txt            # Example campaign documents
└── .env                             # Your credentials
```

---

## 🔐 Security Notes

1. **Never commit `.env`** - it's in `.gitignore`
2. **Gmail App Passwords** - Use app-specific passwords, not your main password
3. **Twilio Trial** - Only sends to verified numbers in trial mode
4. **Rate Limiting** - Built-in delays to avoid spam flags
5. **Opt-In Required** - System checks `optInEmail` and `optInSMS`

---

## 🚨 Troubleshooting

### Email Not Sending
1. Check Gmail credentials in `.env`
2. Ensure 2FA is enabled
3. Use App Password (not regular password)
4. Check console for error messages

### SMS Not Sending
1. Verify Twilio credentials in `.env`
2. Check phone number format (+15551234567)
3. In trial mode, verify recipient numbers
4. Check Twilio dashboard for errors

### CSV Upload Fails
1. Check CSV format (see `sample-contacts.csv`)
2. Ensure headers match expected format
3. Check file encoding (UTF-8)

---

## 🎉 You're All Set!

The system is now fully functional with:
- ✅ Google ADK (Genkit) with Gemini 2.5 Flash AI
- ✅ Web UI for campaign creation
- ✅ Genkit Developer UI for testing agents
- ✅ CSV upload for contacts
- ✅ Gmail for email sending
- ✅ Twilio for SMS sending
- ✅ Instagram Graph API for posting
- ✅ Multi-agent AI coordination
- ✅ Compliance checking
- ✅ Analytics tracking

**Next Steps:**
1. Get your Google API key from https://aistudio.google.com/apikey
2. Configure your `.env` file
3. Run `npm run dev` for Web UI or `npm run example` for terminal
4. Upload contacts via CSV
5. Create your first campaign
6. Watch the magic happen! 🚀

**Testing the Agents:**
```bash
# Install Genkit CLI globally
npm install -g genkit

# Start the Genkit Developer UI
genkit start -- npx tsx src/index.ts

# Open http://localhost:4000 to test agents interactively
```
