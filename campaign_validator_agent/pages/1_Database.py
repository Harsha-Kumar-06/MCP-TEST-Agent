"""Database Explorer — View all campaigns, posts, and validation details."""

import json
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from campaign_validator.database import init_db, seed_data, get_campaigns, get_posts

load_dotenv()
init_db()
seed_data()

IMAGES_DIR = Path(__file__).parent.parent / "images"

st.set_page_config(page_title="Database Explorer", page_icon="🗄️", layout="wide")

st.title("🗄️ Database Explorer")
st.caption("View all campaigns, posts, statuses, AI reports, and human decisions stored in the database.")

# ── Load all campaigns ────────────────────────────────────────────────────
campaigns = get_campaigns()

if not campaigns:
    st.warning("No campaigns found in the database.")
    st.stop()

# ── Campaign Overview Table ───────────────────────────────────────────────
st.header("Campaigns")

campaign_rows = []
for c in campaigns:
    posts = get_posts(c["id"])
    status_counts = {}
    for p in posts:
        status_counts[p["status"]] = status_counts.get(p["status"], 0) + 1
    campaign_rows.append({
        "ID": c["id"],
        "Campaign": c["name"],
        "Brand": c["brand"],
        "Posts": len(posts),
        "Approved": status_counts.get("approved", 0),
        "Rejected": status_counts.get("rejected", 0),
        "Needs Review": status_counts.get("needs_review", 0),
        "Pending": status_counts.get("pending", 0),
        "Created": c.get("created_at", ""),
    })

st.dataframe(campaign_rows, use_container_width=True, hide_index=True)

st.markdown("---")

# ── Detailed Campaign + Posts View ────────────────────────────────────────
st.header("Posts Detail")

tabs = st.tabs([f"{c['brand']} — {c['name']}" for c in campaigns])

for tab, campaign in zip(tabs, campaigns):
    with tab:
        # Campaign requirements
        with st.expander("📋 Campaign Requirements", expanded=False):
            st.markdown(f"**Brand:** {campaign['brand']}")
            st.markdown(f"**Created:** {campaign.get('created_at', 'N/A')}")
            st.markdown("**Requirements:**")
            st.info(campaign["requirements"])

        posts = get_posts(campaign["id"])

        if not posts:
            st.info("No posts for this campaign.")
            continue

        for post in posts:
            status = post["status"]
            color = {
                "approved": "🟢", "rejected": "🔴",
                "needs_review": "🟡", "pending": "⚪",
            }.get(status, "⚪")

            with st.container(border=True):
                # Header row
                col_main, col_img = st.columns([3, 1])

                with col_main:
                    st.markdown(f"#### {color} Post #{post['id']} — {post['influencer_name']}")
                    st.markdown(f"**Status:** `{status.upper()}`  ·  **Image:** `{post['image_path']}`  ·  **Created:** {post.get('created_at', 'N/A')}")

                    # Description
                    st.markdown("**Description:**")
                    st.markdown(f"> {post['description']}")

                with col_img:
                    img_path = IMAGES_DIR / post["image_path"]
                    if img_path.exists():
                        st.image(str(img_path), width=150)
                    else:
                        st.caption(f"📷 {post['image_path']}")

                # AI Report
                if post.get("ai_report"):
                    report = post["ai_report"]
                    with st.expander("🤖 AI Report", expanded=False):
                        st.markdown(f"**Overall Status:** `{report.get('overall_status', 'N/A').upper()}`")
                        st.markdown(f"**Summary:** {report.get('summary', 'N/A')}")

                        checks = report.get("checks", [])
                        if checks:
                            st.markdown("**Checks:**")
                            check_rows = []
                            for c in checks:
                                icon = {"pass": "✅", "fail": "❌", "doubt": "⚠️"}.get(c.get("status", ""), "❓")
                                check_rows.append({
                                    "Result": icon,
                                    "Attribute": c.get("attribute", ""),
                                    "Status": c.get("status", "").upper(),
                                    "Reasoning": c.get("reasoning", ""),
                                })
                            st.dataframe(check_rows, use_container_width=True, hide_index=True)

                        # Raw JSON
                        with st.expander("Raw JSON"):
                            st.json(report)

                # Human Decisions
                if post.get("human_decisions"):
                    with st.expander("👤 Human Decisions", expanded=False):
                        for d in post["human_decisions"]:
                            verdict_icon = "✅" if d.get("verdict") == "approve" else "❌"
                            st.markdown(f"{verdict_icon} **Verdict:** `{d.get('verdict', 'N/A').upper()}`")
                            if d.get("feedback"):
                                st.markdown(f"**Feedback:** {d['feedback']}")
                            if d.get("failed_checks"):
                                st.markdown(f"**Failed checks:** {', '.join(d['failed_checks'])}")

                        # Raw JSON
                        with st.expander("Raw JSON"):
                            st.json(post["human_decisions"])

# ── Raw Tables ────────────────────────────────────────────────────────────
st.markdown("---")
st.header("Raw Data")

raw_tab1, raw_tab2 = st.tabs(["Campaigns Table", "Posts Table"])

with raw_tab1:
    raw_campaigns = []
    for c in campaigns:
        raw_campaigns.append({
            "id": c["id"],
            "name": c["name"],
            "brand": c["brand"],
            "requirements": c["requirements"][:100] + "...",
            "created_at": c.get("created_at", ""),
        })
    st.dataframe(raw_campaigns, use_container_width=True, hide_index=True)

with raw_tab2:
    all_posts = []
    for c in campaigns:
        for p in get_posts(c["id"]):
            all_posts.append({
                "id": p["id"],
                "campaign_id": p["campaign_id"],
                "influencer": p["influencer_name"],
                "image": p["image_path"],
                "status": p["status"],
                "has_ai_report": "Yes" if p.get("ai_report") else "No",
                "has_human_decision": "Yes" if p.get("human_decisions") else "No",
                "description": p["description"][:80] + "...",
                "created_at": p.get("created_at", ""),
            })
    st.dataframe(all_posts, use_container_width=True, hide_index=True)
