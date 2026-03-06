"""Access Controller Agent - Streamlit Demo
Manage access to Atlassian products (Jira, Confluence, Bitbucket) via AI.
"""
import streamlit as st
import requests
import os

st.set_page_config(
    page_title="Access Controller Agent",
    page_icon="🔐",
    layout="wide"
)

# Configuration
DRAYVN_API = os.getenv("DRAYVN_API_URL", "https://your-drayvn-server.com/api/v1/prediction/FLOW_ID")

st.title("🔐 Access Controller Agent")
st.markdown("""
**AI-powered organizational access authority** for managing user access to:
- **Jira** - Projects, Roles, Groups
- **Confluence** - Spaces, Permissions  
- **Bitbucket** - Repositories, Workspaces
- **GitHub** - Organizations, Repositories, Teams
""")

# Sidebar with quick actions
with st.sidebar:
    st.header("Quick Actions")
    platform = st.selectbox("Platform", ["Jira", "Confluence", "Bitbucket", "GitHub"])
    action = st.selectbox("Action", ["Grant Access", "Revoke Access", "List Access", "Invite User"])
    
    st.divider()
    st.markdown("### Example Requests")
    st.code("Grant user@example.com access to Project-X in Jira")
    st.code("Revoke access from user@company.com to the Sales confluence space")
    st.code("List all users with access to my-repo in Bitbucket")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Describe your access request..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Processing access request..."):
            try:
                response = requests.post(
                    DRAYVN_API,
                    json={"question": prompt},
                    headers={"Content-Type": "application/json"},
                    timeout=60
                )
                if response.status_code == 200:
                    answer = response.json().get("text", "Request processed successfully.")
                else:
                    answer = f"⚠️ Error: Unable to process request (Status: {response.status_code})"
            except requests.exceptions.RequestException as e:
                answer = f"⚠️ Connection error: {str(e)}"
            
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

# Footer
st.divider()
st.caption("Access Controller Agent - Built with Google ADK | Manages Atlassian & GitHub access")
