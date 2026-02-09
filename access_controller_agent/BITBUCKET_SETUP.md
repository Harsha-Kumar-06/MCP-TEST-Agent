# Bitbucket Workspace Auto-Invitation Setup

The Access Controller Agent can automatically invite users to Bitbucket workspaces when granting repository access. This eliminates the need for manual invitations via admin.atlassian.com.

## How It Works

When you request: "Give john@example.com read access to mobile-app repo"

**Without Auto-Invitation (old behavior):**
1. ❌ Error: "User not in workspace"
2. ❌ Manual step: Go to admin.atlassian.com
3. ❌ Manual step: Invite user to workspace
4. ❌ Wait for acceptance
5. ✅ Retry access grant

**With Auto-Invitation (new behavior):**
1. ✅ System detects user not in workspace
2. ✅ System automatically sends email invitation
3. ✅ User receives email, accepts invitation
4. ✅ Access granted automatically!

## Required Configuration

### 1. Get Your Organization ID

1. Go to https://admin.atlassian.com
2. Select your organization
3. Look at the URL: `https://admin.atlassian.com/o/YOUR_ORG_ID/overview`
4. Copy `YOUR_ORG_ID`

### 2. Create an API Key

1. Go to https://admin.atlassian.com/o/{YOUR_ORG_ID}/settings/api-keys
2. Click "Create API key"
3. Name it: "Access Controller Agent"
4. Select the following permissions:
   - ✅ `Read workspaces`
   - ✅ `Manage users`
   - ✅ `Manage roles`
5. Click "Create"
6. **IMPORTANT:** Copy the API key immediately (it's shown only once!)

### 3. Set Environment Variables

Add these to your `.env` file or environment:

```bash
# Atlassian Organization Admin API (for automatic workspace invitations)
ATLASSIAN_ORG_ID=your_organization_id_here
ATLASSIAN_API_KEY=your_api_key_here

# Existing Bitbucket credentials
BITBUCKET_USERNAME=your_email@company.com
BITBUCKET_API_TOKEN=your_bitbucket_api_token
BITBUCKET_WORKSPACE=your_workspace_slug
```

### 4. Verify Configuration

Test the configuration:

```python
from access_controller_agent.bitbucket_service import get_atlassian_admin_service

admin = get_atlassian_admin_service()
if admin and admin.is_configured():
    print("✅ Atlassian Admin API is configured!")
    result = admin.get_workspaces()
    print(f"Found {len(result.get('workspaces', []))} workspaces")
else:
    print("❌ Atlassian Admin API is NOT configured")
```

## Usage

Once configured, workspace invitations happen automatically:

### Example 1: Grant Repository Access (Auto-Invites if Needed)

```
User: Give hmoosa.hh@gmail.com read access to mobile-app repo

Agent: ✅ User not in workspace. Automatically invited hmoosa.hh@gmail.com to 
       the workspace. They will receive an email invitation. Repository access 
       will be granted automatically once they accept.
```

### Example 2: User Already in Workspace

```
User: Give sarah@company.com write access to backend-api

Agent: ✅ Granted write access to 'Sarah Johnson' for repository 'backend-api'.
```

### Example 3: Add User to Workspace Only

```
User: Add john@company.com to the Bitbucket workspace

Agent: ✅ Invited 'John Smith' to the workspace. They will receive an email invitation.
```

## Fallback Behavior

If the Atlassian Admin API is NOT configured:

1. Agent attempts to grant access
2. Detects user not in workspace
3. Returns error with manual instructions:
   ```
   ❌ User 'john@example.com' is not a member of the Bitbucket workspace.
   Automatic invitation is not configured. 
   
   Please invite the user manually:
   1. Go to https://admin.atlassian.com
   2. Navigate to: Users → Invite Users
   3. Select the Bitbucket workspace
   4. Invite: john@example.com
   
   Then retry the access grant.
   ```

## Security Notes

- **API Key Storage**: Store the API key securely in environment variables or a secrets manager
- **Permissions**: The API key has organization-level access - keep it secure
- **Rotation**: Rotate API keys periodically (create new, update env vars, delete old)
- **Audit**: All invitations are logged and visible in admin.atlassian.com audit logs

## Troubleshooting

### Error: "Atlassian Admin API not configured"

**Solution:** Set `ATLASSIAN_ORG_ID` and `ATLASSIAN_API_KEY` environment variables

### Error: "Workspace not found in organization"

**Solution:** Verify the workspace slug matches a Bitbucket workspace in your organization:
1. Check https://admin.atlassian.com/o/{ORG_ID}/products
2. Verify the Bitbucket workspace name/slug

### Error: "User {account_id} not found in organization"

**Solution:** The user doesn't have an Atlassian account yet:
1. User needs to create an Atlassian account first
2. Then retry - system will auto-invite them to workspace

### Manual Fallback

If auto-invitation fails, you can always manually invite users:
1. Go to https://admin.atlassian.com
2. Select your organization
3. Navigate to: Users → Invite Users
4. Select the Bitbucket workspace from the products dropdown
5. Enter user's email and send invitation

## API Rate Limits

The Atlassian Organization API has rate limits:
- **General endpoints**: 200 requests per minute per organization
- **User endpoints**: 60 requests per minute per user

The agent automatically handles these limits with proper error handling.
