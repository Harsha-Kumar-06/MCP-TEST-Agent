"""Manage Campaigns & Posts — Add, edit, or remove data from the database."""

from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from campaign_validator.database import (
    init_db, seed_data, get_campaigns, get_posts,
    add_campaign, update_campaign,
    add_post, delete_post,
)

load_dotenv()
init_db()
seed_data()

IMAGES_DIR = Path(__file__).parent.parent / "images"
IMAGES_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="Manage Data", page_icon="📝", layout="wide")

st.title("📝 Manage Campaigns & Posts")
st.caption("Add new campaigns, add influencer posts, or edit existing entries.")
st.markdown("---")

campaigns = get_campaigns()
campaign_map = {c["id"]: c for c in campaigns}


# ══════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════
tab_add_campaign, tab_add_post, tab_edit_campaign, tab_manage_posts = st.tabs([
    "➕ New Campaign",
    "➕ New Post",
    "✏️ Edit Campaign",
    "🗂️ Manage Posts",
])


# ── Tab 1: Add Campaign ───────────────────────────────────────────────────
with tab_add_campaign:
    st.subheader("Add New Campaign")
    st.markdown("Define a new brand campaign. Write the requirements as a natural paragraph — the AI will extract checkable attributes from it automatically.")

    with st.form("add_campaign_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            camp_name = st.text_input(
                "Campaign Name *",
                placeholder="e.g. Pepsi Summer Refresh 2026",
            )
        with col2:
            camp_brand = st.text_input(
                "Brand Name *",
                placeholder="e.g. Pepsi",
            )

        camp_requirements = st.text_area(
            "Campaign Requirements *",
            placeholder=(
                "Write a natural paragraph describing what every influencer post must show.\n\n"
                "Example: Every post must feature the influencer holding or drinking a Pepsi can "
                "with the Pepsi logo clearly visible. The setting should be fun and summery. "
                "The caption must include #PepsiSummer and mention Pepsi by name..."
            ),
            height=220,
        )

        submitted = st.form_submit_button("➕ Add Campaign", type="primary", use_container_width=True)
        if submitted:
            if not camp_name.strip() or not camp_brand.strip() or not camp_requirements.strip():
                st.error("All fields are required.")
            else:
                cid = add_campaign(camp_name.strip(), camp_brand.strip(), camp_requirements.strip())
                st.success(f"Campaign **{camp_name}** added successfully (ID: {cid}). Go to the main app to run validation.")
                st.rerun()


# ── Tab 2: Add Post ───────────────────────────────────────────────────────
with tab_add_post:
    st.subheader("Add Influencer Post")
    st.markdown(
        "Add a new influencer post to a campaign. Write a paragraph description that includes "
        "what is visible in the image, the setting, mood, and the caption text. "
        "The AI will extract all relevant information from the paragraph."
    )

    if not campaigns:
        st.warning("No campaigns exist yet. Add a campaign first.")
    else:
        with st.form("add_post_form", clear_on_submit=True):
            sel_campaign_id = st.selectbox(
                "Campaign *",
                options=[c["id"] for c in campaigns],
                format_func=lambda x: f"{campaign_map[x]['brand']} — {campaign_map[x]['name']}",
            )

            influencer_name = st.text_input(
                "Influencer Name *",
                placeholder="e.g. Sarah Chen",
            )

            img_col1, img_col2 = st.columns([1, 1])
            with img_col1:
                uploaded_img = st.file_uploader(
                    "Upload Image",
                    type=["jpg", "jpeg", "png"],
                    help="Upload the influencer's post image",
                )
            with img_col2:
                st.markdown("")
                st.markdown("")
                manual_path = st.text_input(
                    "Or enter image filename",
                    placeholder="e.g. sarah_post.jpg",
                    help="Filename only — the file must already be in the images/ folder",
                )

            description = st.text_area(
                "Post Description *",
                placeholder=(
                    "Write a natural paragraph describing the influencer's post. Include:\n"
                    "• What is visible in the image (products, clothing, setting, mood)\n"
                    "• The influencer's pose or action\n"
                    "• The caption text they posted\n\n"
                    'Example: "Sarah posted an image at a sunny beach holding a Pepsi can with the '
                    'logo clearly visible. She is wearing a blue Pepsi branded cap. The setting is '
                    'bright and energetic with friends in the background. Her caption reads: '
                    "\\\"Pepsi hits different at the beach! \\u2600 #PepsiSummer #BeachVibes\\\"\""
                ),
                height=220,
            )

            submitted_post = st.form_submit_button("➕ Add Post", type="primary", use_container_width=True)
            if submitted_post:
                if not influencer_name.strip() or not description.strip():
                    st.error("Influencer name and description are required.")
                elif not uploaded_img and not manual_path.strip():
                    st.error("Provide an image upload or an image filename.")
                else:
                    if uploaded_img:
                        save_path = IMAGES_DIR / uploaded_img.name
                        with open(save_path, "wb") as f:
                            f.write(uploaded_img.getbuffer())
                        final_img = uploaded_img.name
                    else:
                        final_img = manual_path.strip()

                    pid = add_post(sel_campaign_id, influencer_name.strip(), final_img, description.strip())
                    st.success(
                        f"Post by **{influencer_name}** added to "
                        f"**{campaign_map[sel_campaign_id]['name']}** (Post ID: {pid}). "
                        f"Go to the main app to run validation."
                    )
                    st.rerun()


# ── Tab 3: Edit Campaign ──────────────────────────────────────────────────
with tab_edit_campaign:
    st.subheader("Edit Existing Campaign")

    if not campaigns:
        st.info("No campaigns to edit.")
    else:
        sel_edit_id = st.selectbox(
            "Select Campaign",
            options=[c["id"] for c in campaigns],
            format_func=lambda x: f"{campaign_map[x]['brand']} — {campaign_map[x]['name']}",
            key="edit_campaign_sel",
        )
        sel_camp = campaign_map[sel_edit_id]

        with st.form("edit_campaign_form"):
            ec1, ec2 = st.columns(2)
            with ec1:
                edit_name = st.text_input("Campaign Name", value=sel_camp["name"])
            with ec2:
                edit_brand = st.text_input("Brand", value=sel_camp["brand"])

            edit_req = st.text_area(
                "Campaign Requirements",
                value=sel_camp["requirements"],
                height=250,
                help="Changes here will affect future validation runs — existing AI reports are not re-generated automatically.",
            )

            save_btn = st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True)
            if save_btn:
                if not edit_name.strip() or not edit_brand.strip() or not edit_req.strip():
                    st.error("All fields are required.")
                else:
                    update_campaign(sel_edit_id, edit_name.strip(), edit_brand.strip(), edit_req.strip())
                    st.success("Campaign updated successfully.")
                    st.rerun()


# ── Tab 4: Manage Posts ───────────────────────────────────────────────────
with tab_manage_posts:
    st.subheader("View & Delete Posts")

    if not campaigns:
        st.info("No campaigns yet.")
    else:
        view_cid = st.selectbox(
            "Select Campaign",
            options=[c["id"] for c in campaigns],
            format_func=lambda x: f"{campaign_map[x]['brand']} — {campaign_map[x]['name']}",
            key="manage_posts_sel",
        )
        posts = get_posts(view_cid)

        if not posts:
            st.info("No posts in this campaign.")
        else:
            st.markdown(f"**{len(posts)} post(s)** in this campaign:")

            for post in posts:
                status_color = {
                    "approved": "#22c55e", "rejected": "#ef4444",
                    "needs_review": "#f59e0b", "pending": "#9ca3af",
                }.get(post["status"], "#9ca3af")

                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 1, 1])

                    with c1:
                        st.markdown(f"**{post['influencer_name']}** · `{post['image_path']}`")
                        st.markdown(
                            f'<span style="background:{status_color}22;color:{status_color};'
                            f'padding:2px 10px;border-radius:12px;font-size:0.78rem;font-weight:700">'
                            f'{post["status"].upper()}</span>',
                            unsafe_allow_html=True,
                        )
                        with st.expander("Description"):
                            st.markdown(post["description"])

                    with c2:
                        img_p = Path(__file__).parent.parent / "images" / post["image_path"]
                        if img_p.exists():
                            st.image(str(img_p), width=100)
                        else:
                            st.caption(f"📷 {post['image_path']}")

                    with c3:
                        st.markdown("")
                        if st.button("🗑️ Delete", key=f"del_{post['id']}", type="secondary"):
                            delete_post(post["id"])
                            st.success(f"Post by {post['influencer_name']} deleted.")
                            st.rerun()
