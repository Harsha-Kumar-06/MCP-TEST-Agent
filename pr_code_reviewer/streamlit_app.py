"""PR Code Reviewer Agent - Streamlit Demo
AI-powered code review bot that acts as a Senior Lead Developer.
"""
import streamlit as st
import requests
import os

st.set_page_config(
    page_title="PR Code Reviewer",
    page_icon="🔍",
    layout="wide"
)

DRAYVN_API = os.getenv("DRAYVN_API_URL", "https://your-drayvn-server.com/api/v1/prediction/FLOW_ID")

st.title("🔍 PR Code Reviewer")
st.markdown("""
**AI Senior Lead Developer** that performs 5-point code inspection:
""")

# Display inspection categories
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown("### 🔒 Security")
    st.caption("Backdoors, leaked secrets")
with col2:
    st.markdown("### 🎨 Style")
    st.caption("Code formatting")
with col3:
    st.markdown("### ⚡ Performance")
    st.caption("Optimization issues")
with col4:
    st.markdown("### 🧠 Logic")
    st.caption("Correctness checks")
with col5:
    st.markdown("### 📝 Docs")
    st.caption("Comments & docs")

st.divider()

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.markdown("### GitHub Integration")
    st.text_input("Repository", placeholder="owner/repo", disabled=True)
    st.caption("Connect via webhook for automatic PR reviews")
    
    st.divider()
    st.markdown("### Demo Mode")
    st.info("Paste code diff below to test the reviewer")

# Tabs for different input modes
tab1, tab2 = st.tabs(["📝 Paste Code Diff", "💬 Chat"])

with tab1:
    st.markdown("### Paste your code diff for review")
    
    code_diff = st.text_area(
        "Code Diff",
        height=300,
        placeholder="""+ def process_user(user_data):
+     password = "admin123"  # hardcoded password
+     query = f"SELECT * FROM users WHERE id = {user_data['id']}"
+     return execute(query)"""
    )
    
    if st.button("🔍 Review Code", type="primary"):
        if code_diff:
            with st.spinner("Running 5-agent parallel review..."):
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.markdown("🔒 Security...")
                with col2:
                    st.markdown("🎨 Style...")
                with col3:
                    st.markdown("⚡ Performance...")
                with col4:
                    st.markdown("🧠 Logic...")
                with col5:
                    st.markdown("📝 Docs...")
                
                try:
                    response = requests.post(
                        DRAYVN_API,
                        json={"question": f"Review this code diff:\n{code_diff}"},
                        headers={"Content-Type": "application/json"},
                        timeout=60
                    )
                    if response.status_code == 200:
                        answer = response.json().get("text", "Review complete!")
                    else:
                        answer = f"⚠️ Error (Status: {response.status_code})"
                except requests.exceptions.RequestException as e:
                    answer = f"⚠️ Connection error: {str(e)}"
                
                st.divider()
                st.markdown("### 📋 Review Results")
                st.markdown(answer)
        else:
            st.warning("Please paste a code diff to review")

with tab2:
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about code review or paste code..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                try:
                    response = requests.post(
                        DRAYVN_API,
                        json={"question": prompt},
                        headers={"Content-Type": "application/json"},
                        timeout=60
                    )
                    if response.status_code == 200:
                        answer = response.json().get("text", "Analysis complete!")
                    else:
                        answer = f"⚠️ Error (Status: {response.status_code})"
                except requests.exceptions.RequestException as e:
                    answer = f"⚠️ Connection error: {str(e)}"
                
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

# Footer
st.divider()
st.caption("PR Code Reviewer - Parallel Swarm Architecture | GitHub Webhook Integration")
