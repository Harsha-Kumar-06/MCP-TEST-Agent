#!/usr/bin/env python3
"""Test script to debug workspace lookup"""

from dotenv import load_dotenv
load_dotenv()

from bitbucket_service import get_atlassian_admin_service

svc = get_atlassian_admin_service()
if svc and svc.is_configured():
    print('=== Testing get_workspaces ===')
    result = svc.get_workspaces()
    print(f'Status: {result.get("status")}')
    if result.get('status') == 'success':
        workspaces = result.get('workspaces', [])
        print(f'Found {len(workspaces)} workspaces')
        for ws in workspaces:
            print(f'  - ID: {ws.get("id")}')
            print(f'    Name: {ws.get("name")}')
            print(f'    Slug: {ws.get("slug")}')
            print(f'    URL: {ws.get("url")}')
            print()
    else:
        print(f'Error: {result.get("error")}')
        
    print('=== Testing get_workspace_ari for thetestmusa ===')
    ari_result = svc.get_workspace_ari('thetestmusa')
    print(f'Status: {ari_result.get("status")}')
    if ari_result.get('status') == 'success':
        print(f'ARI: {ari_result.get("ari")}')
        print(f'Workspace ID: {ari_result.get("workspace_id")}')
    else:
        print(f'Error: {ari_result.get("error")}')
        if 'available_workspaces' in ari_result:
            print(f'Available: {ari_result.get("available_workspaces")}')
else:
    print('Admin service not configured')
