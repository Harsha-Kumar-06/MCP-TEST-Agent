# Quick Testing Guide 🧪

## Prerequisites

### 1. Configure Environment
Make sure `.env` file has these variables:
```bash
# Google ADK (Required for AI features)
GOOGLE_GENAI_API_KEY=your_api_key_here
GOOGLE_MODEL=flash
LLM_PROVIDER=auto

# Gmail SMTP (Required for email sending)
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-16-char-app-password
FROM_NAME=Your Company Name

# Optional: Twilio for SMS
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+15551234567
```

### 2. Start the Development Server
```bash
npm run dev
```

### 3. Verify Initialization
You should see in the terminal:
```
🔧 Initializing Marketing Campaign Agent Services...
────────────────────────────────────────────────────────────
✅ Google ADK (Genkit) initialized with Gemini 2.5 Flash
✅ Email service configured
🕐 Campaign Scheduler started - checking every minute
```

---

## Quick Test: Run the Agent (1 minute)

The fastest way to test:
```bash
npm run example
```

Expected output:
```
Starting Email + SMS Campaign Example...

🔧 Initializing Marketing Campaign Agent Services...
✅ Google ADK (Genkit) initialized with Gemini 2.5 Flash

============================================================
🚀 MULTI-AGENT COORDINATOR SYSTEM
============================================================
Campaign: Q1 Product Launch - Email & SMS
Channels: EMAIL, SMS
...
✅ Campaign setup complete!
```

---

## Test with Genkit Developer UI (Recommended)

```bash
# Install Genkit CLI (once)
npm install -g genkit

# Start the Genkit Developer UI
genkit start -- npx tsx src/index.ts
```

Open http://localhost:4000 to:
- Test individual agents
- View execution traces
- Debug AI responses
- Inspect tool calls

---

## Test 1: Email Tracking (5 minutes)

### Step 1: Send Tracked Email
1. Go to http://localhost:3000/campaigns/create
2. Fill in:
   - Campaign Name: "Test Email Tracking"
   - Select: ✉️ Email (only)
   - Product Name: "Test Product"
   - Description: "Testing email tracking"
   - Add your own email in "Single Recipient" section
3. Click "🚀 Execute Now"

### Step 2: Check Your Email
1. Open the email in your inbox
2. Right-click → "View Page Source" or "Show Original"
3. Search for: `track/open?campaignId=`
4. You should see the tracking pixel: `<img src="/api/track/open?campaignId=camp-xxx..." width="1" height="1">`

### Step 3: View Analytics
1. Go to http://localhost:3000/campaigns
2. Click on your test campaign
3. Scroll down to "📊 Email Analytics Dashboard"
4. You should see:
   - Total Opens: 1
   - Unique Opens: 1
   - Open Rate: 100%

### Step 4: Test Click Tracking
1. Click any link in the email
2. Watch the terminal - you should see:
   ```
   ✅ Click event recorded for campaign: camp-xxxxx
   ```
3. Refresh campaign detail page
4. "Top Clicked Links" should show the URL you clicked

**✅ Success Criteria:**
- Email contains tracking pixel
- Opens are recorded
- Clicks are recorded and redirect works
- Analytics dashboard displays metrics

---

## Test 2: Campaign Scheduler (3-4 minutes)

### Step 1: Schedule a Campaign
1. Go to http://localhost:3000/campaigns/create
2. Fill in campaign details (same as Test 1)
3. **Select: "Schedule for Later"**
4. Pick date/time **2 minutes in the future**
5. Click "📅 Schedule Campaign"

### Step 2: Monitor Execution
1. Watch your terminal logs
2. Every minute you'll see:
   ```
   🕐 Checking for scheduled campaigns...
   ```
3. When time arrives:
   ```
   📅 Found 1 scheduled campaign(s) ready to execute
   🚀 Executing scheduled campaign: Test Email Tracking
   ✅ Scheduled campaign executed: Test Email Tracking
   ```

### Step 3: Verify Results
1. Go to http://localhost:3000/campaigns
2. Campaign status should change from "scheduled" → "completed"
3. Check your email inbox - email should arrive
4. Click on campaign to see results

**✅ Success Criteria:**
- Campaign scheduled successfully
- Scheduler executes at correct time
- Email is sent
- Campaign status updates to "completed"

---

## Test 3: Template Library (2 minutes)

### Step 1: Save a Template
1. Execute any campaign (Test 1)
2. Go to campaign detail page
3. Click "📚 Save as Template" button
4. Enter name: "My First Template"
5. Click OK

### Step 2: Browse Templates
1. Go to http://localhost:3000/campaigns/templates
2. You should see your template card showing:
   - Template name
   - Channels (✉️ email)
   - Description
   - "Use Template" and 🗑️ buttons

### Step 3: Use Template
1. Click "Use Template"
2. You're redirected to create campaign page
3. Form is pre-filled with template data
4. Campaign name shows "(Copy)"
5. Make changes and execute/schedule

### Step 4: Delete Template
1. Go back to templates page
2. Click 🗑️ button
3. Confirm deletion
4. Template is removed from list

**✅ Success Criteria:**
- Template saved successfully
- Template appears in library
- Template loads correctly into new campaign
- Template can be deleted

---

## Test 4: End-to-End Flow (5 minutes)

### Complete Workflow
1. **Create and save template:**
   - Create campaign with email
   - Execute immediately
   - Save as template "Product Launch"

2. **Use template for scheduled campaign:**
   - Go to templates page
   - Click "Use Template"
   - Change campaign name to "Scheduled Launch"
   - Schedule for 2 minutes future
   - Wait for execution

3. **View analytics:**
   - After execution, open campaign detail
   - Check analytics dashboard
   - Open the email sent
   - Click links in email
   - Refresh analytics to see clicks

**✅ Success Criteria:**
- Full flow works without errors
- Template → Schedule → Execute → Analytics
- All tracking data recorded correctly

---

## Debugging Tips

### If tracking doesn't work:
```bash
# Check terminal for errors
# Look for these logs:
✅ Email sent to your@email.com: <message-id>
✅ Open event recorded for campaign: camp-xxxxx
✅ Click event recorded for campaign: camp-xxxxx
```

### If scheduler doesn't execute:
```bash
# Check if scheduler is running:
🕐 Campaign Scheduler started - checking every minute

# Check database:
cat data/campaigns.json
# Look for: "status": "scheduled", "scheduledAt": "..."
```

### If templates don't load:
```bash
# Check templates API:
curl http://localhost:3000/api/campaigns/templates

# Should return JSON with templates array
```

### View database files:
```bash
cat data/campaigns.json        # All campaigns
cat data/tracking-events.json  # All tracking events
cat data/contacts.json         # All contacts
```

---

## Quick Verification Commands

```bash
# Check if server is running
curl http://localhost:3000

# Check templates API
curl http://localhost:3000/api/campaigns/templates

# Check analytics API (replace CAMPAIGN_ID)
curl http://localhost:3000/api/campaigns/analytics?campaignId=CAMPAIGN_ID

# View tracking events
cat data/tracking-events.json | jq '.'

# View scheduled campaigns
cat data/campaigns.json | jq '.[] | select(.status == "scheduled")'
```

---

## Common Issues

### 1. Google ADK not initializing
**Error:** `Google ADK not configured`
**Solution:**
- Get API key from: https://aistudio.google.com/apikey
- Add to `.env`: `GOOGLE_GENAI_API_KEY=your_key`
- Set `GOOGLE_MODEL=flash` and `LLM_PROVIDER=auto`

### 2. Gmail SMTP not working
**Error:** `Invalid login`
**Solution:**
- Use App Password, not regular password
- Enable 2FA on Gmail account
- Generate App Password at: https://myaccount.google.com/apppasswords

### 3. Scheduler not running
**Error:** No logs showing
**Solution:**
- Restart server (scheduler auto-starts)
- Check for TypeScript errors: `npx tsc --noEmit`

### 4. Tracking pixel not loading
**Error:** Broken image in email
**Solution:**
- Ensure server is accessible from email client
- Check if tracking API endpoints work
- Test: `curl http://localhost:3000/api/track/open?campaignId=test&recipientId=test`

### 5. Templates not saving
**Error:** Database error
**Solution:**
- Check `data/` directory exists
- Ensure write permissions
- Check `campaigns.json` is valid JSON

### 6. Genkit CLI not found
**Error:** `could not determine executable to run`
**Solution:**
```bash
npm install -g genkit
genkit start -- npx tsx src/index.ts
```

---

## Expected Output Examples

### Terminal - Successful Email Send
```
📧 EMAIL SENDING AGENT: Sending to 1 recipients...
✅ Email sent to test@example.com: <message-id>
Email Results:
   Sent: 1
   Failed: 0
```

### Terminal - Tracking Events
```
✅ Open event recorded for campaign: camp-1234567890
✅ Click event recorded for campaign: camp-1234567890, URL: https://example.com
```

### Terminal - Scheduler Execution
```
🕐 Checking for scheduled campaigns...
📅 Found 1 scheduled campaign(s) ready to execute
🚀 Executing scheduled campaign: My Campaign
📧 EMAIL SENDING AGENT: Sending to 5 recipients...
✅ Scheduled campaign executed: My Campaign
```

### Analytics Dashboard
```
📊 Email Analytics Dashboard
┌─────────────┬────────────┬─────────────┬─────────┐
│ Total Opens │ Unique Opens │ Open Rate   │ ...    │
│ 15          │ 12          │ 75%         │ ...    │
└─────────────┴────────────┴─────────────┴─────────┘

Top Clicked Links:
1. https://example.com/product (8 clicks)
2. https://example.com/demo (5 clicks)
```

---

## Success! 🎉

If all tests pass:
✅ Email tracking works (opens & clicks)
✅ Campaign scheduler auto-executes  
✅ Template library functional  
✅ Analytics dashboard displays data  

**Your Phase 1 implementation is complete and production-ready!**

---

## Next: Run Your First Real Campaign

1. Import real contacts via CSV
2. Create campaign using template
3. Schedule for optimal send time
4. Monitor analytics in real-time
5. Iterate based on open/click rates

Good luck! 🚀
