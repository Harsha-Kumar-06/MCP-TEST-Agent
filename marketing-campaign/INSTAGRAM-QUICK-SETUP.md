# Instagram API - Quick Setup Guide

## 🚀 Get Your Instagram Credentials (10-15 minutes)

### Prerequisites

Before you start, ensure you have:
- ✅ **Instagram Business or Creator account** (NOT personal)
- ✅ **Facebook Page** linked to your Instagram account
- ✅ **Admin access** to the Facebook Page
- ✅ **Verified email** on your Facebook account

### Step 1: Create Facebook App (3 min)

1. Go to **https://developers.facebook.com/apps/create/**
2. Click **"Create App"**
3. Select **"Other"** (at the bottom) → Click **"Next"**
4. Select **"Business"** type → Click **"Next"**
5. Fill in:
   - **App Name**: "Marketing Campaign Manager"
   - **Contact Email**: Your email
6. Click **"Create App"**

---

### Step 2: Configure Instagram API (3 min)

1. In your app dashboard, click **"Use cases"** on the left sidebar
2. Click **"Customize"** next to **"Instagram"** use case
3. Click **"Add"** for these permissions:
   - ✅ `instagram_basic`
   - ✅ `instagram_content_publish`
   - ✅ `pages_read_engagement`
   - ✅ `pages_show_list`
   - ✅ `business_management`
4. Under **"Products"** in sidebar → Click **"Add product"**
5. Find **"Facebook Login for Business"** → Click **"Set up"**

---

### Step 3: Get Access Token (4 min)

**IMPORTANT:** Use **Facebook Login** method, NOT Instagram Login!

1. Go to **https://developers.facebook.com/tools/explorer/**
2. In the top-right, select your app from the **"Meta App"** dropdown
3. Click **"User or Page"** dropdown → Select **"Get User Access Token"**
4. Check these permissions in the popup:
   - ✅ `instagram_basic`
   - ✅ `instagram_content_publish`
   - ✅ `pages_read_engagement`
   - ✅ `pages_show_list`
   - ✅ `business_management`
5. Click **"Generate Access Token"**
6. Complete the Facebook Login in the popup
7. **IMPORTANT:** When asked to select Pages, **SELECT YOUR FACEBOOK PAGE**!
8. Copy the token - it **MUST start with `EAA...`**

⚠️ **If your token starts with `IGAA...`, you used the wrong method!** Go back to step 3.

---

### Step 4: Get Instagram Business Account ID (3 min)

Open terminal/PowerShell and run:

```bash
curl "https://graph.facebook.com/v18.0/me/accounts?fields=instagram_business_account&access_token=YOUR_TOKEN_HERE"
```

Replace `YOUR_TOKEN_HERE` with your token from Step 3.

**Expected response:**
```json
{
  "data": [
    {
      "instagram_business_account": {
        "id": "17841480486093682"
      },
      "id": "123456789012345"
    }
  ]
}
```

Copy the `id` inside `instagram_business_account` (format: `17841xxxxxxxxxx`).

⚠️ **If you get empty `data: []`:**
- Your Facebook Page is not linked to an Instagram account
- Go to your Facebook Page → Settings → Instagram → Connect Account

---

### Step 5: Add to .env (1 min)

Open your `.env` file and add:

```env
INSTAGRAM_ACCESS_TOKEN=EAA...your_long_token_here
INSTAGRAM_ACCOUNT_ID=17841480486093682
```

---

### Step 6: Get Long-Lived Token (Recommended - 2 min)

Short tokens expire in **1 hour**. Get a **60-day token**:

1. Get your App ID and App Secret from: App Dashboard → Settings → Basic
2. Run:

```bash
curl "https://graph.facebook.com/v18.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=YOUR_SHORT_TOKEN"
```

3. Copy the new `access_token` (it's longer) and update your `.env` file.

---

## ✅ Test Your Setup

Run this command to verify everything works:

```bash
curl "https://graph.facebook.com/v18.0/YOUR_INSTAGRAM_ACCOUNT_ID?fields=username,name,media_count&access_token=YOUR_TOKEN"
```

**Expected response:**
```json
{
  "username": "your_instagram_username",
  "name": "Your Display Name",
  "media_count": 10,
  "id": "17841480486093682"
}
```

---

## 🎯 Test in the App

1. Restart your dev server: `npm run dev`
2. Go to **http://localhost:3000**
3. Create a new campaign
4. Select only **📸 Instagram** channel
5. Upload a campaign document or fill in manually
6. Select a post type (Image, Video, Carousel, Story)
7. Provide a **publicly accessible image URL** (test with: `https://images.unsplash.com/photo-1527960669171-26f1aaa3fb74?w=1080&q=80`)
8. Click **Execute Now**

**Console output on success:**
```
📸 Executing Instagram campaign...
📝 Using custom Instagram content from campaign...
📸 Posting to Instagram feed (image)...
🖼️  Image URL: https://...
   Creating media container...
   Waiting for media to be ready...
   ✅ Media ready (attempt 2)
   Publishing post...
   Publish attempt 1/5...
✅ Instagram image post published: 18560767423027692
   View at: https://www.instagram.com/p/DUrQS-Pj8Ia/
```

---

## ⚠️ Common Issues & Solutions

### "Invalid OAuth access token"
- **Cause:** Token expired or wrong type
- **Fix:** Generate a new token in Graph API Explorer
- **Check:** Token MUST start with `EAA...` (not `IGAA...`)

### "Instagram account not found"
- **Cause:** Wrong Account ID
- **Fix:** Use the ID from `instagram_business_account`, NOT your App ID or Page ID

### "Empty data array from me/accounts"
- **Cause:** Facebook Page not linked to Instagram
- **Fix:** Go to Facebook Page → Settings → Instagram → Connect Account

### "Insufficient developer role"
- **Cause:** App not in Development mode or you're not a tester
- **Fix:** App Dashboard → Roles → Add yourself as Admin or Tester

### "Media ID is not available" (transient)
- **Cause:** Instagram backend processing delay
- **Fix:** The system automatically retries - this is normal for large images

### "The image could not be downloaded"
- **Cause:** Image URL not publicly accessible
- **Fix:** Use a truly public URL (Unsplash, Imgur, Cloudinary work well)

---

## 📸 Supported Post Types

| Type | Image/Video Required | Notes |
|------|---------------------|-------|
| **Image** | 1 image URL | Most common post type |
| **Video/Reels** | 1 video URL | Creates a Reel |
| **Carousel** | 2-10 image URLs | Multiple images in one post |
| **Story** | 1 image/video URL | Disappears after 24 hours |

---

## 🆓 Free Forever

- ✅ No API fees
- ✅ 200 posts per 24 hours limit
- ✅ Works with free Facebook app
- ✅ No monthly charges

---

## 🔒 Security Notes

1. **Never commit your `.env` file!** (already in `.gitignore`)
2. **Never share your access token**
3. **Use long-lived tokens** to avoid frequent regeneration
4. **Regenerate token immediately** if you accidentally expose it

---

## 🎯 Ready to Post!

Once configured, your campaigns will automatically:
- Create professional Instagram posts
- Add captions from your product info
- Include auto-generated hashtags
- Support images, videos, carousels, and stories
- Handle retries if Instagram is slow

No more manual posting! 🚀
