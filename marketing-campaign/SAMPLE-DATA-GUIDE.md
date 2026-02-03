# 📦 Sample Data Guide

This folder contains ready-to-use sample data for testing the Campaign Coordinator system.

## 📄 Campaign Documents (For Upload & Auto-Fill)

### 1. `sample-campaign-document.txt` ⭐ **Quick Start**
Simple campaign document with essential fields. Perfect for first-time testing.

**Contents:**
- Campaign: SmartHome Hub Pro launch
- Channels: Email + Instagram
- Complete product details
- Target audience info
- Budget: $3,500
- **Time to process:** ~2 seconds

**How to use:**
1. Go to `/campaigns/create`
2. Click "Choose File"
3. Select this file
4. Watch form auto-fill!

---

### 2. `sample-campaign-detailed.txt` 🚀 **Comprehensive Example**
Full-featured campaign document with extensive details and multiple sections.

**Contents:**
- Campaign: FitTrack Pro Smartwatch (Fitness tech)
- All channels: Email + SMS + Instagram
- 10+ product features
- Detailed pricing tiers
- Timeline breakdown (10 weeks)
- Social media links
- Competitive advantages
- Technical specifications
- Budget: $10,000
- **Time to process:** ~3 seconds

**Perfect for:**
- Testing full feature extraction
- Seeing how complex documents are parsed
- Multi-channel campaigns
- Large-scale launches

---

### 3. `sample-campaign-simple.txt` ⚡ **Minimal Format**
Bare minimum campaign info. Great for quick tests.

**Contents:**
- Campaign: Black Friday SaaS Sale
- Channel: Email only
- Basic product info
- Budget: $2,500
- **Time to process:** ~1 second

**Use when:**
- Testing basic functionality
- Need quick campaign creation
- Single-channel campaigns

---

## 👥 Contact Lists (For CSV Import)

### 4. `sample-contacts.csv` 📋 **Starter List**
5 contacts with basic information.

**Columns:** email, phone, firstName, lastName, company, tags, optInEmail, optInSMS

**Contacts:**
- John Doe (Acme Corp)
- Jane Smith (Tech Startup)
- Bob Johnson (Enterprise Inc)
- Alice Williams (Small Business)
- Charlie Brown (Freelance)

**Import steps:**
1. Go to `/contacts`
2. Click "Upload CSV"
3. Select this file
4. Contacts import automatically!

---

### 5. `sample-contacts-extended.csv` 📊 **Full Dataset**
25 professional contacts across various industries.

**Industries covered:**
- Technology & SaaS
- Healthcare & Wellness
- Finance & FinTech
- Retail & eCommerce
- Marketing & Consulting
- AI & Blockchain
- Education & Security

**Tags included:**
- Enterprise, SMB, Startup, Freelance
- VIP, Premium customers
- Industry-specific tags

**Perfect for:**
- Testing list segmentation
- Large campaign sends
- Multi-industry targeting
- A/B testing scenarios

---

## 🎯 Quick Testing Workflow

### Test 1: Document Upload + Auto-Fill (5 minutes)
```
1. Visit: http://localhost:3000/campaigns/create
2. Upload: sample-campaign-detailed.txt
3. Review: Auto-populated fields
4. Edit: Adjust as needed
5. Select: sample-contacts-extended.csv list
6. Execute: Launch campaign!
```

### Test 2: Manual Campaign Creation (10 minutes)
```
1. Import: sample-contacts-extended.csv first
2. Create: New campaign manually
3. Select: Email + Instagram channels
4. Fill: Product details
5. Choose: Imported contact list
6. Execute: Send campaign
```

### Test 3: Single Contact Campaign (3 minutes)
```
1. Upload: sample-campaign-simple.txt
2. Select: Single contact mode
3. Enter: Your own email for testing
4. Execute: Receive campaign email!
```

---

## 📝 File Format Examples

### Campaign Document Format
```
Campaign Name: [Your Campaign]

Channels: Email, SMS, Instagram

Product Name: [Product]

Description: [2-3 sentences]

Features:
- Feature 1
- Feature 2
- Feature 3

Target Audience: [Demographics]

Budget: [Amount]

Start Date: 2026-04-01

Goals:
- Goal 1
- Goal 2
```

### CSV Contact Format
```csv
email,phone,firstName,lastName,company,tags,optInEmail,optInSMS
john@example.com,+1-555-0100,John,Doe,Company,tag1;tag2,true,true
```

**Required columns:**
- `email` (required)
- `firstName` (required)
- `lastName` (required)

**Optional columns:**
- `phone` (for SMS campaigns)
- `company`
- `tags` (semicolon-separated)
- `optInEmail` (true/false)
- `optInSMS` (true/false)

---

## 🎨 Testing Scenarios

### Scenario A: Email-Only Campaign
- **Document:** `sample-campaign-simple.txt`
- **Contacts:** `sample-contacts.csv` (5 contacts)
- **Channel:** Email only
- **Time:** 2 minutes total
- **Result:** 5 emails sent

### Scenario B: Multi-Channel Campaign
- **Document:** `sample-campaign-detailed.txt`
- **Contacts:** `sample-contacts-extended.csv` (25 contacts)
- **Channels:** Email + SMS + Instagram
- **Time:** 5 minutes total
- **Result:** 25 emails + 25 SMS + 1 Instagram post

### Scenario C: Single Recipient Test
- **Document:** `sample-campaign-document.txt`
- **Mode:** Single contact
- **Recipient:** Your own email/phone
- **Channels:** Email + SMS
- **Time:** 1 minute
- **Result:** Test email/SMS to yourself

---

## 🔧 Customization Tips

### Modify Campaign Documents
1. Copy any sample file
2. Change product name, description, features
3. Adjust target audience and budget
4. Save with new name
5. Upload and test!

### Add Your Own Contacts
1. Open `sample-contacts-extended.csv`
2. Add rows with your contacts
3. Keep same column format
4. Save and import

### Create Custom Scenarios
Mix and match:
- Different campaign docs with different contact lists
- Single vs list recipient modes
- Various channel combinations

---

## 📊 Expected Results

### After Importing Contacts
- Contacts appear in `/contacts` page
- Can create contact lists
- Contacts available for campaign selection

### After Document Upload
- Form auto-fills in ~1-3 seconds
- All extracted fields shown
- Can edit before executing
- Campaign name, product, features, budget all populated

### After Campaign Execution
- Success notification shows
- Campaign appears in `/campaigns` list
- Results displayed (emails sent, SMS sent, Instagram posts)
- Can view, edit, resend, or delete

---

## 🚀 Advanced Testing

### Test Instagram Posting
1. Configure Instagram in `.env` (see `INSTAGRAM-QUICK-SETUP.md`)
2. Upload `sample-campaign-detailed.txt`
3. Check Instagram channel
4. Execute campaign
5. Check your Instagram feed!

### Test Contact Segmentation
1. Import `sample-contacts-extended.csv`
2. Create lists by tags (Enterprise, Startup, SMB)
3. Create targeted campaigns per segment
4. Compare results

### Test Campaign Editing & Resending
1. Create any campaign
2. Go to campaign detail page
3. Click "Edit"
4. Modify content
5. Check "Resend after updating"
6. Submit and verify resend

---

## 💡 Tips & Tricks

**Best Practices:**
- Test with small lists first (5-10 contacts)
- Use your own email for initial tests
- Review auto-filled data before executing
- Check both HTML and plain text email versions

**Common Issues:**
- **Document not parsing:** Check file format (PDF/DOCX/TXT)
- **Missing fields:** Add clear labels like "Product Name:", "Budget:"
- **CSV import fails:** Ensure required columns exist (email, firstName, lastName)
- **Emails not sending:** Verify Gmail credentials in `.env`

**Performance:**
- Document parsing: 1-3 seconds
- Contact import: < 1 second per 100 contacts
- Campaign execution: ~1 second per recipient
- Instagram posting: 2-3 seconds

---

## 📞 Support

Need help? Check:
- `README.md` - Setup instructions
- `SETUP-GUIDE.md` - Detailed configuration
- `ARCHITECTURE.md` - System overview
- `CAMPAIGN-DOCUMENT-TEMPLATE.md` - Document format guide

---

**Ready to test?** Start with Test 1 above - it's the fastest way to see everything working! 🚀
