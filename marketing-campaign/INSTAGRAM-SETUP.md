# Instagram Setup Guide

## 📸 How to Enable Instagram Campaigns

Instagram campaigns work by posting to your Instagram feed and stories, not sending DMs.

### ✅ What You Need

1. **Instagram Business or Creator Account**
2. **Facebook Page** linked to Instagram
3. **Facebook App** with Instagram permissions
4. **Access Token** from Facebook

---

## 🚀 Setup Steps

### Step 1: Convert to Business Account

1. Open Instagram app
2. Go to **Settings** → **Account**
3. Tap **Switch to Professional Account**
4. Choose **Business** or **Creator**

### Step 2: Link to Facebook Page

1. Go to **Settings** → **Account** → **Linked Accounts**
2. Tap **Facebook**
3. Log in and link your Facebook Page

### Step 3: Create Facebook App

1. Go to https://developers.facebook.com/
2. Click **My Apps** → **Create App**
3. Choose **Business** type
4. Enter app name and contact email
5. Click **Create App**

### Step 4: Add Instagram API

1. In your app dashboard, click **Add Product**
2. Find **Instagram** and click **Set Up**
3. Configure Instagram Basic Display or Instagram Graph API

### Step 5: Get Access Token

#### Option A: Graph API Explorer (Testing)
1. Go to https://developers.facebook.com/tools/explorer/
2. Select your app
3. Add permissions:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_read_engagement`
4. Click **Generate Access Token**
5. Copy the token

#### Option B: Long-Lived Token (Production)
```bash
# Exchange short-lived token for long-lived (60 days)
curl -X GET "https://graph.facebook.com/v18.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=YOUR_SHORT_TOKEN"
```

### Step 6: Get Instagram Account ID

```bash
curl -X GET "https://graph.facebook.com/v18.0/me/accounts?access_token=YOUR_ACCESS_TOKEN"
```

Look for `instagram_business_account` → `id`

### Step 7: Add to .env

```env
INSTAGRAM_ACCESS_TOKEN=your_access_token_here
INSTAGRAM_ACCOUNT_ID=your_instagram_account_id_here
```

---

## 📝 How It Works

When you create a campaign with Instagram channel:

1. **System generates** post caption with:
   - Product description
   - Key features
   - Pricing
   - Call-to-action
   - Hashtags

2. **Posts to Instagram**:
   - Feed post (permanent)
   - Story (24 hours)

3. **Your followers see** the campaign
4. **They can engage** with likes, comments, shares

---

## 🎯 Campaign Example

**Input:**
```
Product: AI Analytics Tool
Description: Transform data into insights
Features: Real-time dashboards, AI predictions
Target: Software developers
```

**Output (Instagram Post):**
```
✨ AI Analytics Tool ✨

Transform data into insights with AI-powered analytics

🎯 Perfect for: Software developers

Key Features:
✓ Real-time dashboards
✓ AI predictions
✓ Easy integration

💰 Starting at $49/month

🔗 Link in bio

#marketing #business #AI #analytics #software
```

---

## 🆓 Free Forever

✅ No posting fees (unlike SMS)
✅ Unlimited posts
✅ Reach all followers
✅ Rich media support

---

## ⚠️ Limitations

- Cannot send DMs to users who haven't messaged you first
- API rate limits: 200 posts per day
- Stories expire after 24 hours
- Need Facebook Business approval for some features

---

## 🔧 Test Mode

The system works in **dry-run mode** without credentials:
- Generates post content
- Shows preview in console
- Doesn't actually post

Perfect for testing before getting API access!

---

## 💡 Alternative: Manual Posting

If you don't want to set up API:

1. Run campaign with Instagram channel
2. Copy generated content from console
3. Manually post to Instagram
4. Still get benefit of AI-generated content!
