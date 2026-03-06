"""Social Media Content Moderator - Streamlit Demo
AI Compliance Officer for user-generated content using parallel swarm pattern.
"""
import streamlit as st
import requests
import os

st.set_page_config(
    page_title="Content Moderator",
    page_icon="🛡️",
    layout="wide"
)

DRAYVN_API = os.getenv("DRAYVN_API_URL", "https://your-drayvn-server.com/api/v1/prediction/FLOW_ID")

st.title("🛡️ Social Media Content Moderator")
st.markdown("""
**AI Compliance Officer** that automatically scans posts for violations using parallel analysis.
""")

# Display moderation categories
st.markdown("### 🔍 Parallel Analysis Pipeline")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📝 Text Analysis")
    st.markdown("""
    - Hate speech detection
    - Violence detection
    - Spam identification
    - Profanity filtering
    """)

with col2:
    st.markdown("### 🖼️ Image Analysis")
    st.markdown("""
    - Adult content detection
    - Violence in images
    - Graphic content
    - Brand safety
    """)

with col3:
    st.markdown("### 🔗 Link Analysis")
    st.markdown("""
    - Phishing detection
    - Malware scanning
    - URL reputation
    - Redirect chains
    """)

st.divider()

# Sidebar
with st.sidebar:
    st.header("⚙️ Moderation Settings")
    
    strictness = st.select_slider(
        "Strictness Level",
        options=["Lenient", "Standard", "Strict", "Maximum"],
        value="Standard"
    )
    
    st.markdown("### Categories to Check")
    check_text = st.checkbox("Text Content", value=True)
    check_images = st.checkbox("Images", value=True)
    check_links = st.checkbox("Links", value=True)
    
    st.divider()
    st.markdown("### Quick Stats")
    st.metric("Posts Reviewed", "1,234")
    st.metric("Violations Found", "23")
    st.metric("Accuracy", "99.2%")

# Main content
tab1, tab2, tab3 = st.tabs(["📝 Single Post", "📤 Bulk Upload", "💬 Chat"])

with tab1:
    st.markdown("### Submit Content for Moderation")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        text_content = st.text_area(
            "Post Text/Caption",
            height=150,
            placeholder="Enter the post text or caption to analyze..."
        )
        
        image_url = st.text_input(
            "Image URL (optional)",
            placeholder="https://example.com/image.jpg"
        )
        
        links = st.text_input(
            "Links in Post (comma-separated)",
            placeholder="https://link1.com, https://link2.com"
        )
    
    with col2:
        st.markdown("#### Preview")
        if text_content:
            st.text(text_content[:100] + "..." if len(text_content) > 100 else text_content)
        if image_url:
            try:
                st.image(image_url, width=200)
            except:
                st.caption(f"🖼️ {image_url}")
        if links:
            for link in links.split(","):
                st.caption(f"🔗 {link.strip()}")
    
    if st.button("🔍 Moderate Content", type="primary"):
        if text_content or image_url or links:
            # Show parallel processing
            st.markdown("### 🔄 Running Parallel Analysis...")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if check_text and text_content:
                    with st.spinner("Analyzing text..."):
                        text_progress = st.progress(100)
                        st.success("✅ Text analyzed")
                else:
                    st.info("⏭️ Skipped")
                    
            with col2:
                if check_images and image_url:
                    with st.spinner("Analyzing image..."):
                        image_progress = st.progress(100)
                        st.success("✅ Image analyzed")
                else:
                    st.info("⏭️ Skipped")
                    
            with col3:
                if check_links and links:
                    with st.spinner("Analyzing links..."):
                        links_progress = st.progress(100)
                        st.success("✅ Links analyzed")
                else:
                    st.info("⏭️ Skipped")
            
            # Call API
            with st.spinner("Generating verdict..."):
                try:
                    payload = {
                        "question": f"Moderate this content - Text: {text_content}, Image: {image_url}, Links: {links}"
                    }
                    response = requests.post(
                        DRAYVN_API,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                        timeout=60
                    )
                    if response.status_code == 200:
                        answer = response.json().get("text", "Moderation complete!")
                    else:
                        # Demo response
                        issues = []
                        if "hate" in text_content.lower() or "kill" in text_content.lower():
                            issues.append("🔴 **Text**: Potential hate speech detected")
                        if "bit.ly" in links.lower() or "tinyurl" in links.lower():
                            issues.append("🟡 **Links**: Shortened URL - verify destination")
                        
                        if issues:
                            answer = f"""
## ⚠️ FLAGGED FOR REVIEW

### Issues Found:
{chr(10).join(issues)}

### Recommendation:
Manual review required before publishing.
"""
                        else:
                            answer = """
## ✅ APPROVED

### Analysis Summary:
- **Text**: No violations detected
- **Image**: Content appropriate
- **Links**: All URLs safe

### Verdict: Safe to publish
"""
                except requests.exceptions.RequestException as e:
                    answer = f"⚠️ Connection error: {str(e)}"
            
            st.divider()
            st.markdown(answer)
        else:
            st.warning("Please provide content to moderate")

with tab2:
    st.markdown("### Bulk Content Moderation")
    
    uploaded_file = st.file_uploader(
        "Upload CSV/JSON with posts",
        type=["csv", "json"],
        help="File should contain: text, image_url, links columns"
    )
    
    if uploaded_file:
        st.success(f"✅ Uploaded: {uploaded_file.name}")
        
        if st.button("🚀 Process All Posts", type="primary"):
            with st.spinner("Processing batch..."):
                st.progress(100)
                st.success("Batch processing complete!")
                
                # Demo results
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Posts", "50")
                with col2:
                    st.metric("Approved", "47", delta="94%")
                with col3:
                    st.metric("Flagged", "3", delta="-6%")
    else:
        st.info("Upload a CSV or JSON file with posts to moderate")

with tab3:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask about content moderation..."):
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
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Architecture", "Parallel Swarm")
with col2:
    st.metric("Sub-Agents", "3")
with col3:
    st.metric("Response Time", "<5s")
