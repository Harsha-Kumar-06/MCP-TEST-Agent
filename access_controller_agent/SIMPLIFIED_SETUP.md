# Simplified Configuration Guide

## Overview

The Access Controller Agent now uses **Atlassian Organization Admin API** as the primary method for managing user access across all platforms (Jira, Confluence, Bitbucket). This eliminates the need for multiple product-specific API tokens.

## Required Credentials (Only 2!)

### 1. Atlassian Organization Admin API

**Purpose:** Manage user invitations and product access across all Atlassian products

**Setup:**
1. Go to https://admin.atlassian.com
2. Select your organization
3. Go to Settings → API keys
4. Create a new API key
5. Copy the Organization ID and API Key

**Add to .env:**
```env
ATLASSIAN_ORG_ID=your_org_id_here
ATLASSIAN_API_KEY=your_api_key_here
```

### 2. Jira Configuration

**Purpose:** Jira-specific operations (issue creation, project management, etc.)

**Setup:**
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Create API token
3. Copy the token

**Add to .env:**
```env
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=your_email@company.com
JIRA_API_TOKEN=your_jira_token_here
```

## What This Enables

### ✅ Works with Admin API Only:
- **Invite users** to Atlassian organization
- **Grant product access** (Bitbucket workspace, Jira site, Confluence site)
- **Revoke product access**
- **List users** in organization
- **Manage workspace membership**

### ⚠️ Requires Product-Specific Tokens (Optional):
- **Repository-level permissions** in Bitbucket (e.g., grant read/write to specific repo)
- **Space-level permissions** in Confluence
- **Project-level roles** in Jira

## Workflow Examples

### Grant Bitbucket Access (Admin API Only)

```
User: "Invite john@company.com to Bitbucket workspace 'myworkspace'"
```

**What happens:**
1. Admin API invites user to organization
2. Admin API grants Bitbucket workspace access
3. User receives email invitation
4. User accepts → Full workspace access granted

**Limitations:**
- User gets workspace-level access (can see all repos)
- Cannot set repository-specific permissions without Bitbucket API token

### Grant Repository-Specific Access (Requires Bitbucket Token)

```
User: "Give john@company.com read access to repo 'mobile-app'"
```

**What happens:**
1. Admin API invites user to workspace (if not already member)
2. **Bitbucket API** sets repository-level read permission
3. User can only access 'mobile-app' repo

**Requires:**
```env
BITBUCKET_USERNAME=admin@company.com
BITBUCKET_API_TOKEN=your_bitbucket_token
BITBUCKET_WORKSPACE=myworkspace
```

## Current Configuration Status

Based on your `.env` file:

✅ **Configured:**
- ATLASSIAN_ORG_ID
- ATLASSIAN_API_KEY  
- JIRA credentials
- Gmail (for notifications)

❌ **Not Configured:**
- Bitbucket API token (optional - only needed for repo-level permissions)
- Confluence API token (optional - only needed for space-level permissions)

## Recommendations

### For Basic User Management:
**Use current setup** - Admin API handles everything!

### For Advanced Permissions:
Only add product-specific tokens if you need:
1. **Bitbucket:** Repository-level access control
2. **Confluence:** Space-level access control
3. **Jira:** Already configured ✅

## Troubleshooting

### "401 Unauthorized" Error
- Verify ATLASSIAN_API_KEY is an **Organization API key**, not a user API token
- Verify ATLASSIAN_ORG_ID matches your organization

### "User not found in Bitbucket"
- User needs to **accept the email invitation** to activate Bitbucket access
- Check their email for the Atlassian invitation

### Repository access fails
- Add `BITBUCKET_API_TOKEN` for repository-level permissions
- Or grant workspace-level access (user can see all repos)

## Summary

You're now using a **simplified 2-credential approach**:
1. ✅ **Atlassian Admin API** - User management across all products
2. ✅ **Jira API Token** - Jira-specific operations

This eliminates the need for separate Bitbucket and Confluence tokens for basic user access management!
