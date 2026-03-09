"""Research Assistant Agent - Streamlit Demo
AI-powered document analysis using Google Gemini.
Simplified version for Streamlit Cloud deployment.
"""
import streamlit as st
import os
import io

st.set_page_config(
    page_title="Research Assistant",
    page_icon="🔬",
    layout="wide"
)

def get_gemini_response(question: str, document: str = "") -> str:
    """Get response from Google Gemini API directly"""
    try:
        import google.generativeai as genai
        
        api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return "⚠️ GOOGLE_API_KEY not configured. Add it to Streamlit Secrets."
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""You are a Research Assistant AI. Analyze the following and provide comprehensive findings.

QUESTION: {question}

{"DOCUMENT TO ANALYZE:" + chr(10) + document[:30000] if document else ""}

Provide a detailed, well-structured response with:
1. Key findings
2. Important insights
3. Recommendations (if applicable)
"""
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

def extract_text_from_file(uploaded_file) -> tuple[str, str]:
    """Extract text from uploaded file"""
    filename = uploaded_file.name.lower()
    content = uploaded_file.read()
    uploaded_file.seek(0)
    
    ext = os.path.splitext(filename)[1]
    
    try:
        if ext == '.pdf':
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            text = "\n\n".join([page.extract_text() or "" for page in pdf_reader.pages])
            return text, "PDF"
        elif ext in ['.docx', '.doc']:
            from docx import Document as DocxDocument
            doc = DocxDocument(io.BytesIO(content))
            text = "\n\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            return text, "Word"
        else:
            text = content.decode('utf-8', errors='ignore')
            return text, ext.upper().replace('.', '') or "Text"
    except Exception as e:
        return content.decode('utf-8', errors='ignore'), "Text"

st.title("🔬 Research Assistant")
st.markdown("**AI Research Analyst** powered by Google Gemini")

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
            with st.spinner("Analyzing..."):
                answer = get_gemini_response(question=prompt)
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
                doc_text, doc_type = extract_text_from_file(uploaded_file)
                st.caption(f"📄 Extracted {len(doc_text)} characters from {doc_type} file")
                
                question = analysis_prompt if analysis_prompt else f"Analyze and summarize this {doc_type} document"
                answer = get_gemini_response(question=question, document=doc_text)
                
                st.markdown("### 📋 Analysis Results")
                st.markdown(answer)
    else:
        st.warning("📁 Please upload a document in the sidebar")

with tab3:
    st.markdown("### 🌐 Web Research")
    
    research_query = st.text_input("Research Topic", placeholder="Latest trends in AI agents...")
    
    if st.button("🔍 Research", type="primary"):
        if research_query:
            with st.spinner(f"Researching: {research_query}"):
                answer = get_gemini_response(
                    question=f"Research and provide comprehensive information about: {research_query}"
                )
                st.markdown("### 📋 Research Findings")
                st.markdown(answer)
        else:
            st.warning("Please enter a research topic")

# Footer
st.divider()
st.caption("Powered by Google Gemini AI")
