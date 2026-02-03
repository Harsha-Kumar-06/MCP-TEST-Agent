# Instagram API - Quick Setup Guide

## 🚀 Get Your Instagram Credentials (10 minutes)

### Step 1: Create Facebook App (2 min)

1. Go to https://developers.facebook.com/apps/create/
2. Click **"Create App"**
3. Select **"Business"** type
4. Fill in:
   - **App Name**: "Marketing Campaign Manager"
   - **Contact Email**: Your email
5. Click **"Create App"**

---

### Step 2: Add Instagram Product (1 min)

1. In app dashboard, scroll to **"Add Products"**
2. Find **"Instagram Graph API"** → Click **"Set Up"**
3. You'll see Instagram settings appear

---

### Step 3: Get Access Token (3 min)

1. Go to **https://developers.facebook.com/tools/explorer/**
2. Select your app from dropdown (top right)
3. Click **"Generate Access Token"**
4. Select permissions:
   - ✅ `instagram_basic`
   - ✅ `instagram_content_publish` 
   - ✅ `pages_read_engagement`
   - ✅ `pages_show_list`
5. Click **"Generate Token"**
6. **Copy the token** (starts with EAA...)

---

### Step 4: Get Instagram Account ID (2 min)

Open terminal and run:

```bash
curl "https://graph.facebook.com/v18.0/me/accounts?access_token=YOUR_ACCESS_TOKEN_HERE"
```

Replace `YOUR_ACCESS_TOKEN_HERE` with the token from Step 3.

Look for your page, then find `instagram_business_account` → `id`. Example:
```json
{
  "data": [
    {
      "name": "Your Page Name",
      "instagram_business_account": {
        "id": "17841234567890123"  // ← This is your Instagram Account ID
      }
    }
  ]
}
```

---

### Step 5: Add to .env (1 min)

Open `.env` file and add:

```env
INSTAGRAM_ACCESS_TOKEN=EAA...your_token_here
INSTAGRAM_ACCOUNT_ID=17841234567890123
```

---

### Step 6: Get Long-Lived Token (Optional - 1 min)

Short tokens expire in 1 hour. Get a 60-day token:

```bash
curl -X GET "https://graph.facebook.com/v18.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=YOUR_SHORT_TOKEN"
```

Replace:
- `YOUR_APP_ID` - Found in app dashboard → Settings → Basic
- `YOUR_APP_SECRET` - Same location (click "Show")
- `YOUR_SHORT_TOKEN` - Token from Step 3

Copy the new `access_token` to your `.env` file.

---

## ✅ Test It!

1. Restart your dev server: `npm run dev`
2. Create a campaign
3. Check **📸 Instagram**
4. Execute!

You should see:
```
📸 Posting to Instagram feed...
   Container created: 12345_67890
✅ Instagram post published: 12345_67890
   View at: https://www.instagram.com/p/...
```

---

## ⚠️ Common Issues

### "Invalid OAuth access token"
- Token expired (get new one)
- Wrong token format
- Token doesn't have required permissions

### "Instagram account not found"
- Wrong Instagram Account ID
- Instagram not linked to Facebook Page
- Not a Business/Creator account

### "Caption too long"
- Instagram limit: 2,200 characters
- System auto-truncates but check manually

---

## 📋 Requirements Checklist

Before setup:
- ✅ Instagram Business or Creator account
- ✅ Facebook Page linked to Instagram
- ✅ Admin access to Facebook Page
- ✅ Verified email on Facebook

---

## 🆓 Free Forever

- ✅ No API fees
- ✅ No posting limits for personal use
- ✅ 200 posts/day rate limit (plenty!)
- ✅ Works with free Facebook app

---

## 🔒 Security Note

Never commit your `.env` file! It's already in `.gitignore`.

Your tokens are sensitive - keep them private!

---

## 🎯 Ready to Go!

Once configured, campaigns will automatically post to your Instagram feed with:
- Professional captions
- Product features
- Call-to-action
- Auto-generated hashtags
- Link to your website

No more manual posting! 🚀
