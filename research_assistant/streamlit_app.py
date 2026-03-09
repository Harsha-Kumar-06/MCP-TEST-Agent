"""Research Assistant Agent - Streamlit Demo (Self-Contained)
AI-powered document analysis with 5-agent sequential pipeline.
Runs the Google ADK agent directly - no separate backend needed.
"""
import streamlit as st
import os
import io
import asyncio
import uuid

# Fix async event loop for Streamlit Cloud
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

# Configure environment before imports
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['SSL_CERT_FILE'] = ''

st.set_page_config(
    page_title="Research Assistant",
    page_icon="🔬",
    layout="wide"
)

# Global flag to track if agent is available
AGENT_AVAILABLE = False
AGENT_ERROR = None

# Initialize Google ADK components (cached)
@st.cache_resource
def init_agent():
    """Initialize the ADK agent and runner (cached for performance)"""
    global AGENT_AVAILABLE, AGENT_ERROR
    try:
        from google.adk import Runner
        from google.adk.sessions import InMemorySessionService
        from research_assistant import root_agent
        
        session_service = InMemorySessionService()
        runner = Runner(
            agent=root_agent,
            app_name="research_assistant",
            session_service=session_service
        )
        AGENT_AVAILABLE = True
        return runner, session_service, True, None
    except ImportError as e:
        AGENT_ERROR = f"Missing package: {e}"
        return None, None, False, AGENT_ERROR
    except Exception as e:
        AGENT_ERROR = str(e)
        return None, None, False, AGENT_ERROR

# File parsing functions
def extract_text_from_file(uploaded_file) -> tuple[str, str]:
    """Extract text from uploaded file"""
    import PyPDF2
    from docx import Document as DocxDocument
    
    filename = uploaded_file.name.lower()
    content = uploaded_file.read()
    uploaded_file.seek(0)  # Reset for potential re-read
    
    ext = os.path.splitext(filename)[1]
    
    if ext == '.pdf':
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = "\n\n".join([page.extract_text() or "" for page in pdf_reader.pages])
        return text, "PDF"
    elif ext in ['.docx', '.doc']:
        doc = DocxDocument(io.BytesIO(content))
        text = "\n\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        return text, "Word"
    elif ext in ['.txt', '.md', '.py', '.js', '.json', '.csv', '.xml', '.html']:
        text = content.decode('utf-8', errors='ignore')
        return text, ext.upper().replace('.', '')
    else:
        text = content.decode('utf-8', errors='ignore')
        return text, "Text"

async def run_agent_pipeline(question: str, document: str, progress_callback=None) -> str:
    """Run the 5-agent pipeline directly"""
    from google.genai import types
    
    runner, session_service, success, error = init_agent()
    
    if not success:
        return f"⚠️ Agent initialization failed: {error}"
    
    # Check API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return "⚠️ GOOGLE_API_KEY not configured. Add it to Streamlit secrets."
    
    session_id = str(uuid.uuid4())
    user_id = "streamlit_user"
    
    # Create session
    await session_service.create_session(
        app_name="research_assistant",
        user_id=user_id,
        session_id=session_id
    )
    
    # Prepare message
    user_message = f"""RESEARCH QUESTION: {question}

DOCUMENT TO ANALYZE:
{document[:50000]}

Analyze this document and provide comprehensive findings with specific citations."""
    
    new_message = types.Content(
        role="user",
        parts=[types.Part(text=user_message)]
    )
    
    # Run pipeline
    final_response = ""
    agent_names = ['IntentDetectorAgent', 'DataProcessorAgent', 'AnalyzerAgent', 'ExtractorAgent', 'ReportGeneratorAgent']
    
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=new_message
    ):
        if hasattr(event, 'author') and hasattr(event, 'content'):
            if event.author == 'ReportGeneratorAgent' and event.content:
                if hasattr(event.content, 'parts'):
                    final_response = "".join([p.text for p in event.content.parts if hasattr(p, 'text')])
            
            # Update progress
            if progress_callback and event.author in agent_names:
                idx = agent_names.index(event.author)
                progress_callback(idx + 1, len(agent_names), event.author)
    
    return final_response if final_response else "Analysis complete. No detailed report generated."

def run_sync(coro):
    """Run async code in sync context - Streamlit Cloud compatible"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(lambda: asyncio.run(coro)).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)

# Try to initialize agent early (but don't crash if it fails)
_runner, _session, _agent_ok, _agent_err = init_agent()

st.title("🔬 Research Assistant")

# Show warning if agent not available (but keep UI working)
if not _agent_ok:
    st.warning(f"""⚠️ **Agent not fully initialized**: {_agent_err}

**To fix:** Ensure these are in `requirements.txt`:
- `google-adk>=0.5.0`
- `google-generativeai>=0.3.0`
- `nest_asyncio>=1.6.0`

And add `GOOGLE_API_KEY` to Streamlit Secrets.""")

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
                
                def update_progress(step, total, agent_name):
                    progress.progress(step / total)
                    status.markdown(f"**Running: {agent_name}...**")
                
                try:
                    # Run agent directly (no HTTP request)
                    answer = run_sync(run_agent_pipeline(
                        question=prompt,
                        document="No document provided - answer from general knowledge.",
                        progress_callback=update_progress
                    ))
                except Exception as e:
                    answer = f"⚠️ Error: {str(e)}"
                
                progress.progress(1.0)
                status.empty()
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
                    # Extract text from uploaded file
                    doc_text, doc_type = extract_text_from_file(uploaded_file)
                    st.caption(f"📄 Extracted {len(doc_text)} characters from {doc_type} file")
                    
                    # Run agent directly
                    question = analysis_prompt if analysis_prompt else f"Analyze and summarize this {doc_type} document"
                    answer = run_sync(run_agent_pipeline(
                        question=question,
                        document=doc_text
                    ))
                except Exception as e:
                    answer = f"⚠️ Error: {str(e)}"
                
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
                    # Run agent directly for research
                    answer = run_sync(run_agent_pipeline(
                        question=f"Research and provide comprehensive information about: {research_query}",
                        document=f"Web research request for: {research_query}\nSearch depth: {search_depth}\nSources: {', '.join(sources)}"
                    ))
                except Exception as e:
                    answer = f"⚠️ Error: {str(e)}"
                
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
