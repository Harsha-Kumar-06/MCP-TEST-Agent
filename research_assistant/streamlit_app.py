"""Research Assistant Agent - Streamlit Demo
AI-powered document analysis with 5-agent sequential pipeline.
"""
import streamlit as st
import requests
import os

st.set_page_config(
    page_title="Research Assistant",
    page_icon="🔬",
    layout="wide"
)

DRAYVN_API = os.getenv("DRAYVN_API_URL", "https://your-drayvn-server.com/api/v1/prediction/FLOW_ID")

st.title("🔬 Research Assistant")
st.markdown("""
**AI Research Analyst** with 5-agent sequential pipeline for comprehensive document analysis.
""")

# Display pipeline stages
st.markdown("### 📊 Agent Pipeline")
cols = st.columns(5)
pipeline_stages = [
    ("🎯", "Intent Detector", "Understands request"),
    ("📄", "Data Processor", "Extracts content"),
    ("🔍", "Analyzer", "Deep analysis"),
    ("📋", "Extractor", "Key findings"),
    ("📝", "Report Generator", "Final report")
]

for i, (icon, name, desc) in enumerate(pipeline_stages):
    with cols[i]:
        st.markdown(f"### {icon}")
        st.markdown(f"**{name}**")
        st.caption(desc)
        if i < 4:
            st.markdown("→")

st.divider()

# Sidebar
with st.sidebar:
    st.header("📁 File Upload")
    
    uploaded_file = st.file_uploader(
        "Upload Document",
        type=["pdf", "docx", "txt", "xlsx", "csv", "md", "py", "js", "json"],
        help="Supports 20+ file formats"
    )
    
    if uploaded_file:
        st.success(f"✅ {uploaded_file.name}")
        st.caption(f"Size: {uploaded_file.size / 1024:.1f} KB")
    
    st.divider()
    
    analysis_mode = st.selectbox(
        "Analysis Mode",
        ["Research Assistant", "Literature Review", "Competitive Analysis", "Code Review"]
    )
    
    st.divider()
    st.markdown("### 📍 Features")
    st.markdown("""
    - 📄 20+ file formats
    - 🔍 Location tracking `[P#:L#-#]`
    - 🌐 Web search integration
    - 🔧 Code fix generation
    """)

# Main content area
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📤 Upload Analysis", "🔍 Web Research"])

with tab1:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a research question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Running 5-agent pipeline..."):
                progress = st.progress(0)
                status = st.empty()
                
                for i, (_, name, _) in enumerate(pipeline_stages):
                    status.markdown(f"**Running: {name}...**")
                    progress.progress((i + 1) / len(pipeline_stages))
                
                try:
                    response = requests.post(
                        DRAYVN_API,
                        json={"question": prompt},
                        headers={"Content-Type": "application/json"},
                        timeout=120
                    )
                    if response.status_code == 200:
                        answer = response.json().get("text", "Analysis complete!")
                    else:
                        answer = f"⚠️ Error (Status: {response.status_code})"
                except requests.exceptions.RequestException as e:
                    answer = f"⚠️ Connection error: {str(e)}"
                
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

with tab2:
    st.markdown("### 📤 Document Analysis")
    
    if uploaded_file:
        st.info(f"Ready to analyze: **{uploaded_file.name}**")
        
        analysis_prompt = st.text_area(
            "What would you like to know about this document?",
            placeholder="Summarize the key findings...\nExtract all actionable items...\nReview the code for security issues..."
        )
        
        if st.button("🔍 Analyze Document", type="primary"):
            with st.spinner("Processing document..."):
                try:
                    # In production, you'd upload the file
                    response = requests.post(
                        DRAYVN_API,
                        json={
                            "question": f"Analyze document '{uploaded_file.name}': {analysis_prompt}",
                        },
                        headers={"Content-Type": "application/json"},
                        timeout=120
                    )
                    if response.status_code == 200:
                        answer = response.json().get("text", "Analysis complete!")
                    else:
                        answer = f"⚠️ Error (Status: {response.status_code})"
                except requests.exceptions.RequestException as e:
                    answer = f"⚠️ Connection error: {str(e)}"
                
                st.markdown("### 📋 Analysis Results")
                st.markdown(answer)
    else:
        st.warning("📁 Please upload a document in the sidebar")

with tab3:
    st.markdown("### 🌐 Web Research")
    
    research_query = st.text_input("Research Topic", placeholder="Latest trends in AI agents...")
    
    col1, col2 = st.columns(2)
    with col1:
        search_depth = st.selectbox("Search Depth", ["Quick", "Standard", "Deep"])
    with col2:
        sources = st.multiselect("Sources", ["Google", "DuckDuckGo", "Academic"], default=["Google"])
    
    if st.button("🔍 Research", type="primary"):
        if research_query:
            with st.spinner(f"Researching: {research_query}"):
                try:
                    response = requests.post(
                        DRAYVN_API,
                        json={"question": f"Research: {research_query}"},
                        headers={"Content-Type": "application/json"},
                        timeout=120
                    )
                    if response.status_code == 200:
                        answer = response.json().get("text", "Research complete!")
                    else:
                        answer = f"⚠️ Error (Status: {response.status_code})"
                except requests.exceptions.RequestException as e:
                    answer = f"⚠️ Connection error: {str(e)}"
                
                st.markdown("### 📋 Research Findings")
                st.markdown(answer)
        else:
            st.warning("Please enter a research topic")

# Footer
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Pipeline Agents", "5")
with col2:
    st.metric("File Formats", "20+")
with col3:
    st.metric("Search Engines", "Google + DDG")
