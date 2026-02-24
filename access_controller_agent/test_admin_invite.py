#!/usr/bin/env python3
"""Test the Admin API invitation process"""

from dotenv import load_dotenv
load_dotenv()

from bitbucket_service import get_atlassian_admin_service

svc = get_atlassian_admin_service()
if svc and svc.is_configured():
    # Get workspace ARI
    ari_result = svc.get_workspace_ari('thetestmusa')
    print(f"Workspace ARI: {ari_result}")
    
    if ari_result.get('status') == 'success':
        workspace_ari = ari_result.get('ari')
        
        # Try to invite the user
        print("\n=== Testing invite_user_to_product ===")
        invite_result = svc.invite_user_to_product(
            email='hmoosa.hh@gmail.com',
            resource_ari=workspace_ari
        )
        print(f"Invite result: {invite_result}")
else:
    print('Admin service not configured')
