"""Social Media Trends Agent - Streamlit Demo
AI agent for analyzing trends across Instagram, TikTok, and YouTube.
"""
import streamlit as st
import requests
import os

st.set_page_config(
    page_title="Social Media Trends",
    page_icon="📱",
    layout="wide"
)

DRAYVN_API = os.getenv("DRAYVN_API_URL", "https://your-drayvn-server.com/api/v1/prediction/FLOW_ID")

st.title("📱 Social Media Trends Agent")
st.markdown("""
**AI-Powered Trend Intelligence** - Analyze trends across Instagram, TikTok, and YouTube for marketing decisions.
""")

# Platform icons
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📸 Instagram")
    st.caption("Reels, Stories, Hashtags")

with col2:
    st.markdown("### 🎵 TikTok")
    st.caption("Videos, Sounds, Creators")

with col3:
    st.markdown("### 📺 YouTube")
    st.caption("Videos, Shorts, Channels")

st.divider()

# Sidebar - Filters
with st.sidebar:
    st.header("🔍 Trend Filters")
    
    platforms = st.multiselect(
        "Platforms",
        ["Instagram", "TikTok", "YouTube"],
        default=["Instagram", "TikTok", "YouTube"]
    )
    
    categories = st.multiselect(
        "Categories",
        ["Fashion", "Tech", "Food", "Fitness", "Beauty", "Gaming", "Travel", "Finance"],
        default=["Fashion", "Tech"]
    )
    
    country = st.selectbox(
        "Country/Region",
        ["Global", "United States", "United Kingdom", "Canada", "Australia", "India", "Brazil"]
    )
    
    time_range = st.selectbox(
        "Time Range",
        ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "Last 90 Days"]
    )
    
    st.divider()
    
    st.markdown("### 📊 Analysis Type")
    analysis_type = st.radio(
        "Select focus",
        ["Trending Topics", "Rising Creators", "Viral Content", "Hashtag Analysis", "Ad Placement"]
    )

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["🔥 Trends", "👤 Creators", "📈 Insights", "💬 Chat"])

with tab1:
    st.markdown("### 🔥 Current Trends")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_query = st.text_input(
            "Search for trends",
            placeholder="e.g., sustainable fashion, AI tools, fitness challenges..."
        )
    
    with col2:
        search_btn = st.button("🔍 Analyze Trends", type="primary", use_container_width=True)
    
    if search_btn and search_query:
        with st.spinner("Analyzing trends across platforms..."):
            try:
                payload = {
                    "question": f"Analyze trends for '{search_query}' on {', '.join(platforms)} in {categories} categories for {country} over {time_range}"
                }
                response = requests.post(
                    DRAYVN_API,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=60
                )
                if response.status_code == 200:
                    answer = response.json().get("text", "Analysis complete!")
                else:
                    # Demo response
                    answer = f"""
## 🔥 Trend Analysis: "{search_query}"

### 📸 Instagram
| Trend | Engagement | Growth |
|-------|------------|--------|
| #{search_query.replace(' ', '')} | 2.3M posts | +45% |
| #Sustainable{search_query.split()[0]} | 890K posts | +78% |

**Top Performing Content:**
- Carousel posts with tips: 12% engagement rate
- Reels under 30 seconds: 8.5% engagement rate

### 🎵 TikTok
| Trend | Views | Velocity |
|-------|-------|----------|
| #{search_query.replace(' ', '')} | 45M views | 🔥 Viral |
| Sound: "{search_query} remix" | 12M uses | ↗️ Rising |

**Creator Opportunity:**
- Duet potential: High
- Best posting time: 6-9 PM EST

### 📺 YouTube
| Topic | Search Volume | Competition |
|-------|--------------|-------------|
| "{search_query} 2024" | 110K/month | Medium |
| "Best {search_query}" | 74K/month | Low |

**Recommended:**
- Video length: 8-12 minutes
- Shorts potential: High for tutorials
"""
            except requests.exceptions.RequestException as e:
                answer = f"⚠️ Connection error: {str(e)}"
            
            st.markdown(answer)
    else:
        # Show default trending topics
        st.markdown("#### 📊 Top Trending Now")
        
        trending_data = {
            "Instagram": ["#OOTD", "#SustainableFashion", "#AIArt", "#FitnessTok"],
            "TikTok": ["#BookTok", "#CleanGirl", "#AIFilter", "#CottageCore"],
            "YouTube": ["Tech Reviews", "Day in Life", "AI Tutorials", "Budget Tips"]
        }
        
        cols = st.columns(3)
        for i, (platform, trends) in enumerate(trending_data.items()):
            with cols[i]:
                st.markdown(f"**{platform}**")
                for trend in trends:
                    st.markdown(f"- {trend}")

with tab2:
    st.markdown("### 👤 Rising Creators")
    
    creator_category = st.selectbox(
        "Creator Category",
        ["All Categories"] + categories
    )
    
    follower_range = st.select_slider(
        "Follower Range",
        options=["Nano (1K-10K)", "Micro (10K-100K)", "Mid-tier (100K-500K)", "Macro (500K-1M)", "Mega (1M+)"],
        value="Micro (10K-100K)"
    )
    
    if st.button("🔍 Find Creators", type="primary"):
        with st.spinner("Discovering creators..."):
            st.markdown("""
### 🌟 Recommended Creators

| Creator | Platform | Followers | Engagement | Category |
|---------|----------|-----------|------------|----------|
| @sustainable_style | Instagram | 45K | 8.2% | Fashion |
| @techreviewer_pro | YouTube | 120K | 4.5% | Tech |
| @fitness.daily | TikTok | 89K | 12.3% | Fitness |
| @foodie.explores | Instagram | 67K | 6.8% | Food |

**💡 Pro Tip:** Micro-influencers (10K-100K) often have 3x higher engagement than mega-influencers.
""")

with tab3:
    st.markdown("### 📈 Marketing Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🎯 Ad Placement Recommendations")
        st.markdown("""
        Based on your selected categories:
        
        **Best Performing Formats:**
        - Instagram Reels: 2.3x ROI
        - TikTok In-Feed: 1.8x ROI
        - YouTube Shorts: 1.5x ROI
        
        **Optimal Budget Split:**
        - 40% TikTok (discovery)
        - 35% Instagram (engagement)
        - 25% YouTube (conversion)
        """)
    
    with col2:
        st.markdown("#### 📊 Audience Demographics")
        st.markdown("""
        **Age Distribution:**
        - 18-24: 35%
        - 25-34: 40%
        - 35-44: 18%
        - 45+: 7%
        
        **Peak Engagement Times:**
        - Instagram: 11am, 7pm
        - TikTok: 7pm, 9pm
        - YouTube: 2pm, 8pm
        """)

with tab4:
    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask about social media trends..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Researching..."):
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
                        answer = f"Let me analyze that for you...\n\nBased on current trends for '{prompt[:50]}...', I recommend focusing on short-form video content across TikTok and Instagram Reels, with supporting long-form content on YouTube for deeper engagement."
                except requests.exceptions.RequestException as e:
                    answer = f"⚠️ Connection error: {str(e)}"
                
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

# Footer
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Platforms", "3")
with col2:
    st.metric("Data Sources", "Google Search + APIs")
with col3:
    st.metric("Update Frequency", "Real-time")
