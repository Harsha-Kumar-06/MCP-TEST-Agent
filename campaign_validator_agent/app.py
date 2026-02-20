"""Campaign Post Validator — Full HITL Pipeline with Animated Agent Steps.

Flow:
1. Dashboard — overview of all campaigns, Run Selected or Run All
2. Validating — animated agent pipeline: Task Breakdown → Validator Agents per post
3. HITL Review — human reviews ALL posts (AI-approved + flagged), can override any
4. Results — final per-campaign breakdown of approved/rejected posts
"""

import asyncio
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from campaign_validator.database import (
    init_db, seed_data, get_campaigns, get_campaign, get_posts,
    update_post_report, save_human_decisions, reset_all_posts, reset_all_campaigns,
)
from campaign_validator.agents import extract_attributes, validate_post

load_dotenv()
init_db()
seed_data()

IMAGES_DIR = Path(__file__).parent / "images"

st.set_page_config(page_title="Campaign Validator", page_icon="🎯", layout="wide")

# ── CSS ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .badge {
        display: inline-block; padding: 3px 12px; border-radius: 20px;
        font-size: 0.78rem; font-weight: 700; letter-spacing: 0.04em;
    }
    .badge-approved { background: #22c55e22; color: #22c55e; }
    .badge-rejected { background: #ef444422; color: #ef4444; }
    .badge-flagged  { background: #f59e0b22; color: #f59e0b; }
    .badge-pending  { background: #6b728022; color: #9ca3af; }
    .campaign-card  { padding: 4px 0 8px 0; }
    div[data-testid="stHorizontalBlock"] > div { gap: 0.5rem; }
</style>
""", unsafe_allow_html=True)


# ── Session state defaults ─────────────────────────────────────────────────
for k, v in {
    "phase": "dashboard",
    "selected_campaign": 1,
    "campaigns_to_validate": [],
    "hitl_posts": [],
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Helpers ────────────────────────────────────────────────────────────────
def run_sync(coro):
    """Run an async coroutine from a sync Streamlit context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def badge_html(status: str) -> str:
    cfg = {
        "approved":    ("badge-approved", "✅ APPROVED"),
        "rejected":    ("badge-rejected", "❌ REJECTED"),
        "needs_review":("badge-flagged",  "⚠️ FLAGGED"),
        "pending":     ("badge-pending",  "⏳ PENDING"),
    }
    cls, label = cfg.get(status, ("badge-pending", status.upper()))
    return f'<span class="badge {cls}">{label}</span>'


def check_icon(status: str) -> str:
    return {"pass": "✅", "fail": "❌", "doubt": "⚠️"}.get(status, "❓")


def post_image(image_path: str, width: int = 100):
    p = IMAGES_DIR / image_path
    if p.exists():
        st.image(str(p), width=width)
    else:
        st.caption(f"📷 {image_path}")


# ── Load campaigns ─────────────────────────────────────────────────────────
all_campaigns = get_campaigns()
if not all_campaigns:
    st.error("No campaigns found. Check database setup.")
    st.stop()

campaign_map = {c["id"]: c for c in all_campaigns}


# ══════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("🎯 Campaign Validator")
    st.markdown("---")

    # Campaign selector
    sel_idx = next((i for i, c in enumerate(all_campaigns)
                    if c["id"] == st.session_state.selected_campaign), 0)
    selected_id = st.selectbox(
        "Active Campaign",
        options=[c["id"] for c in all_campaigns],
        format_func=lambda x: f"{campaign_map[x]['brand']} — {campaign_map[x]['name']}",
        index=sel_idx,
    )
    if selected_id != st.session_state.selected_campaign:
        st.session_state.selected_campaign = selected_id
        if st.session_state.phase not in ("validating", "hitl_review"):
            st.session_state.phase = "dashboard"
        st.rerun()

    st.markdown("---")

    # Global stats across all campaigns
    st.markdown("**Global Stats**")
    all_posts_flat = [p for c in all_campaigns for p in get_posts(c["id"])]
    g_total    = len(all_posts_flat)
    g_approved = sum(1 for p in all_posts_flat if p["status"] == "approved")
    g_rejected = sum(1 for p in all_posts_flat if p["status"] == "rejected")
    g_pending  = sum(1 for p in all_posts_flat if p["status"] in ("pending", "needs_review"))

    c1, c2 = st.columns(2)
    c1.metric("Total",    g_total)
    c2.metric("Approved", g_approved)
    c1.metric("Rejected", g_rejected)
    c2.metric("Pending",  g_pending)

    st.markdown("---")

    if st.button("🔄 Reset Selected Campaign", use_container_width=True):
        reset_all_posts(st.session_state.selected_campaign)
        st.session_state.update(phase="dashboard", hitl_posts=[])
        st.rerun()

    if st.button("🔄 Reset All Campaigns", use_container_width=True, type="secondary"):
        reset_all_campaigns()
        st.session_state.update(phase="dashboard", hitl_posts=[])
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════
# PHASE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════
if st.session_state.phase == "dashboard":
    st.title("📋 Campaign Validator Dashboard")

    # ── Action buttons ────────────────────────────────────────────────────
    sel_campaign  = campaign_map[st.session_state.selected_campaign]
    sel_posts     = get_posts(sel_campaign["id"])
    pending_sel   = [p for p in sel_posts if p["status"] == "pending"]

    all_pending = [p for c in all_campaigns for p in get_posts(c["id"]) if p["status"] == "pending"]
    review_posts = [p for c in all_campaigns for p in get_posts(c["id"]) if p["status"] == "needs_review"]

    btn1, btn2 = st.columns(2)
    with btn1:
        if pending_sel:
            if st.button(
                f"🚀 Run Selected Campaign\n**{sel_campaign['brand']}** · {len(pending_sel)} pending post(s)",
                type="primary", use_container_width=True,
            ):
                st.session_state.campaigns_to_validate = [sel_campaign["id"]]
                st.session_state.hitl_posts = []
                st.session_state.phase = "validating"
                st.rerun()
        else:
            st.success(f"No pending posts in **{sel_campaign['name']}**")

    with btn2:
        if all_pending:
            if st.button(
                f"🌐 Run All Campaigns\n{len(all_campaigns)} campaigns · {len(all_pending)} pending post(s)",
                type="secondary", use_container_width=True,
            ):
                st.session_state.campaigns_to_validate = [c["id"] for c in all_campaigns]
                st.session_state.hitl_posts = []
                st.session_state.phase = "validating"
                st.rerun()
        else:
            st.info("No pending posts across all campaigns.")

    # Review button if posts are waiting
    if review_posts:
        st.warning(f"⚠️ **{len(review_posts)} post(s)** are waiting for human review.")
        if st.button("👤 Go to Human Review →", type="primary"):
            st.session_state.phase = "hitl_review"
            st.rerun()

    st.markdown("---")

    # ── Campaign cards ────────────────────────────────────────────────────
    st.subheader("All Campaigns")
    for campaign in all_campaigns:
        posts     = get_posts(campaign["id"])
        total     = len(posts)
        approved  = sum(1 for p in posts if p["status"] == "approved")
        rejected  = sum(1 for p in posts if p["status"] == "rejected")
        pending   = sum(1 for p in posts if p["status"] == "pending")
        flagged   = sum(1 for p in posts if p["status"] == "needs_review")
        done      = approved + rejected
        is_sel    = campaign["id"] == st.session_state.selected_campaign

        border_style = "2px solid #6366f1" if is_sel else None

        with st.container(border=True):
            h1, h2 = st.columns([5, 1])
            with h1:
                sel_tag = " — **SELECTED**" if is_sel else ""
                st.markdown(f"### {campaign['brand']} — {campaign['name']}{sel_tag}")
            with h2:
                if is_sel:
                    st.markdown("🔵 **Active**")

            # Metrics row
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Total",     total)
            m2.metric("✅ Approved",  approved)
            m3.metric("❌ Rejected",  rejected)
            m4.metric("⚠️ Flagged",   flagged)
            m5.metric("⏳ Pending",   pending)

            # Progress bar
            if total > 0:
                pct = done / total
                st.progress(pct, text=f"{int(pct * 100)}% processed")

            # Compact post list
            with st.expander(f"Posts ({total})"):
                for post in posts:
                    pc1, pc2, pc3 = st.columns([3, 1, 3])
                    pc1.markdown(f"**{post['influencer_name']}** · `{post['image_path']}`")
                    pc2.markdown(badge_html(post["status"]), unsafe_allow_html=True)
                    if post.get("ai_report"):
                        checks = post["ai_report"].get("checks", [])
                        passed = sum(1 for c in checks if c["status"] == "pass")
                        pc3.caption(f"{passed}/{len(checks)} checks · {post['ai_report'].get('summary', '')[:60]}...")


# ══════════════════════════════════════════════════════════════════════════
# PHASE: VALIDATING — Animated agent pipeline
# ══════════════════════════════════════════════════════════════════════════
elif st.session_state.phase == "validating":
    campaigns_to_run = [campaign_map[cid] for cid in st.session_state.campaigns_to_validate
                        if cid in campaign_map]

    total_pending = sum(
        len([p for p in get_posts(c["id"]) if p["status"] == "pending"])
        for c in campaigns_to_run
    )

    st.title("🤖 AI Agent Pipeline")
    st.markdown(
        f"Running autonomous validation across **{len(campaigns_to_run)} campaign(s)** "
        f"· **{total_pending} post(s)** to analyze"
    )
    st.markdown("---")

    overall_bar = st.progress(0, text="Initializing agent pipeline...")
    posts_done  = 0
    hitl_posts  = []

    for campaign in campaigns_to_run:
        pending_posts = [p for p in get_posts(campaign["id"]) if p["status"] == "pending"]
        if not pending_posts:
            continue

        with st.status(
            f"📊 **{campaign['brand']}** — {campaign['name']}  "
            f"({len(pending_posts)} post{'s' if len(pending_posts) > 1 else ''})",
            expanded=True,
        ) as camp_status:

            # ── Step 1: Task Breakdown Agent ──────────────────────────────
            st.write("🔍 **Task Breakdown Agent** — reading campaign requirements and extracting attributes...")
            attrs = run_sync(extract_attributes(campaign["requirements"], campaign["brand"]))

            if not attrs:
                st.write("❌ Attribute extraction failed — skipping this campaign.")
                camp_status.update(label=f"❌ {campaign['name']} — Extraction failed", state="error")
                continue

            attr_lines = [l for l in attrs.split("\n") if l.strip() and l.strip()[0].isdigit()]
            st.write(
                f"✅ **Task Breakdown Agent** — identified "
                f"**{len(attr_lines)} checkable attribute(s)** from requirements"
            )
            with st.expander("View extracted attributes"):
                st.markdown(attrs)

            # ── Step 2: Validator Agents (one per post) ───────────────────
            st.write(
                f"🔄 **Validator Agents** — launching {len(pending_posts)} "
                f"agent{'s' if len(pending_posts) > 1 else ''} in sequence..."
            )

            for i, post in enumerate(pending_posts):
                st.write(
                    f"   🤖 **Validator Agent #{i + 1}** — "
                    f"analyzing **{post['influencer_name']}**'s post..."
                )

                report = run_sync(validate_post(
                    campaign_name=campaign["name"],
                    brand=campaign["brand"],
                    attributes=attrs,
                    influencer_name=post["influencer_name"],
                    description=post["description"],
                    image_path=post.get("image_path"),
                ))

                if not report:
                    report = {"checks": [], "overall_status": "needs_review", "summary": "Validation error."}

                ai_status = report.get("overall_status", "needs_review")
                checks    = report.get("checks", [])
                passed    = sum(1 for c in checks if c.get("status") == "pass")
                icon      = {"approved": "✅", "rejected": "❌", "needs_review": "⚠️"}.get(ai_status, "⚠️")

                st.write(
                    f"   {icon} **{post['influencer_name']}** → "
                    f"`{ai_status.upper()}` · {passed}/{len(checks)} checks passed"
                )

                # Save to DB (approved stays approved; everything else → needs_review for HITL)
                db_status = "approved" if ai_status == "approved" else "needs_review"
                update_post_report(post["id"], db_status, report)

                hitl_posts.append({
                    "post_id":       post["id"],
                    "campaign_id":   campaign["id"],
                    "campaign_name": campaign["name"],
                    "brand":         campaign["brand"],
                    "influencer_name": post["influencer_name"],
                    "image_path":    post.get("image_path", ""),
                    "description":   post["description"],
                    "ai_report":     report,
                    "ai_status":     ai_status,
                })

                posts_done += 1
                overall_bar.progress(
                    posts_done / total_pending,
                    text=f"Processed {posts_done}/{total_pending} posts...",
                )

            camp_status.update(
                label=(
                    f"✅ **{campaign['brand']}** — {campaign['name']}  "
                    f"— {len(pending_posts)} post(s) validated"
                ),
                state="complete",
            )

    overall_bar.progress(1.0, text="✅ All agents complete!")

    # Store for HITL
    st.session_state.hitl_posts = hitl_posts

    # Summary before proceeding
    ai_ok      = sum(1 for p in hitl_posts if p["ai_status"] == "approved")
    ai_flagged = len(hitl_posts) - ai_ok

    st.markdown("---")
    r1, r2, r3 = st.columns(3)
    r1.metric("Total Analyzed", len(hitl_posts))
    r2.metric("🤖 AI Approved", ai_ok)
    r3.metric("⚠️ Needs Review", ai_flagged)

    st.info(
        f"**{ai_ok}** post(s) approved by AI · **{ai_flagged}** flagged — "
        "all posts go to Human Review so you can confirm or override every decision."
    )

    if st.button("👤 Proceed to Human Review →", type="primary", use_container_width=True):
        st.session_state.phase = "hitl_review"
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════
# PHASE: HITL REVIEW — Human reviews ALL posts (approve + flagged)
# ══════════════════════════════════════════════════════════════════════════
elif st.session_state.phase == "hitl_review":

    # Reload from DB if session was lost
    hitl_posts = st.session_state.hitl_posts
    if not hitl_posts:
        for campaign in all_campaigns:
            for p in get_posts(campaign["id"]):
                if p["status"] in ("approved", "needs_review") and p.get("ai_report"):
                    hitl_posts.append({
                        "post_id":       p["id"],
                        "campaign_id":   campaign["id"],
                        "campaign_name": campaign["name"],
                        "brand":         campaign["brand"],
                        "influencer_name": p["influencer_name"],
                        "image_path":    p.get("image_path", ""),
                        "description":   p["description"],
                        "ai_report":     p["ai_report"] or {},
                        "ai_status":     p["status"],
                    })
        st.session_state.hitl_posts = hitl_posts

    if not hitl_posts:
        st.warning("No posts to review. Run AI validation first.")
        if st.button("← Back to Dashboard"):
            st.session_state.phase = "dashboard"
            st.rerun()
        st.stop()

    ai_approved_list = [p for p in hitl_posts if p["ai_status"] == "approved"]
    ai_flagged_list  = [p for p in hitl_posts if p["ai_status"] != "approved"]

    # ── Header ────────────────────────────────────────────────────────────
    st.title("👤 Human Review Dashboard")
    st.markdown(
        "Review every post below. **AI-approved** posts default to Approve and "
        "**AI-flagged** posts default to Reject — you can override any decision."
    )

    hm1, hm2, hm3, hm4 = st.columns(4)
    hm1.metric("Total Posts",    len(hitl_posts))
    hm2.metric("🤖 AI Approved", len(ai_approved_list))
    hm3.metric("⚠️ AI Flagged",  len(ai_flagged_list))
    hm4.metric("Campaigns",      len({p["campaign_id"] for p in hitl_posts}))

    st.markdown("---")

    # ── Filter ────────────────────────────────────────────────────────────
    filter_col, _ = st.columns([2, 4])
    with filter_col:
        filter_choice = st.selectbox(
            "Filter posts",
            ["All Posts", "🤖 AI Approved only", "⚠️ AI Flagged only"],
        )

    filtered = {
        "All Posts":             hitl_posts,
        "🤖 AI Approved only":  ai_approved_list,
        "⚠️ AI Flagged only":   ai_flagged_list,
    }[filter_choice]

    st.markdown("---")

    # ── Post cards ────────────────────────────────────────────────────────
    decisions = {}  # post_id → {verdict, feedback}

    # Group by campaign
    by_campaign: dict[int, dict] = {}
    for p in filtered:
        cid = p["campaign_id"]
        if cid not in by_campaign:
            by_campaign[cid] = {"name": p["campaign_name"], "brand": p["brand"], "posts": []}
        by_campaign[cid]["posts"].append(p)

    for cid, group in by_campaign.items():
        st.subheader(f"📊 {group['brand']} — {group['name']}")

        for post in group["posts"]:
            report    = post["ai_report"] or {}
            checks    = report.get("checks", [])
            summary   = report.get("summary", "")
            ai_status = post["ai_status"]

            # Colors
            if ai_status == "approved":
                ai_color, ai_label, default_idx = "#22c55e", "🤖 AI APPROVED", 0
            elif ai_status == "rejected":
                ai_color, ai_label, default_idx = "#ef4444", "🤖 AI REJECTED", 1
            else:
                ai_color, ai_label, default_idx = "#f59e0b", "🤖 AI FLAGGED", 1

            with st.container(border=True):
                # ── Card header ───────────────────────────────────────────
                top_left, top_right = st.columns([3, 1])
                with top_left:
                    st.markdown(f"### {post['influencer_name']}")
                    st.markdown(
                        f'<span style="background:{ai_color}22;color:{ai_color};'
                        f'padding:4px 14px;border-radius:20px;font-size:0.82rem;font-weight:700">'
                        f'{ai_label}</span>',
                        unsafe_allow_html=True,
                    )
                    if summary:
                        st.markdown(f"_{summary}_")
                with top_right:
                    post_image(post["image_path"], width=130)

                st.markdown("")

                # ── AI Checks grid ────────────────────────────────────────
                if checks:
                    st.markdown("**AI Validation Checks:**")
                    n_cols = min(len(checks), 3)
                    cols   = st.columns(n_cols)
                    for i, ch in enumerate(checks):
                        with cols[i % n_cols]:
                            icon = check_icon(ch.get("status", ""))
                            color = {"pass": "#22c55e", "fail": "#ef4444", "doubt": "#f59e0b"}.get(
                                ch.get("status", ""), "#9ca3af"
                            )
                            st.markdown(
                                f'<div style="border:1px solid {color}44;border-radius:8px;'
                                f'padding:8px 10px;margin-bottom:6px">'
                                f'<span style="font-weight:700">{icon} {ch.get("attribute","")}</span>'
                                f'<br><span style="color:#9ca3af;font-size:0.82rem">'
                                f'{ch.get("reasoning","")}</span></div>',
                                unsafe_allow_html=True,
                            )

                with st.expander("📄 Post description"):
                    st.markdown(post["description"])

                st.markdown("---")

                # ── Human decision ────────────────────────────────────────
                # Pre-populate feedback message from AI checks (only on first render)
                feedback_key = f"f_{post['post_id']}"
                if feedback_key not in st.session_state:
                    passed_checks  = [c for c in checks if c.get("status") == "pass"]
                    failed_checks  = [c for c in checks if c.get("status") == "fail"]
                    doubt_checks   = [c for c in checks if c.get("status") == "doubt"]
                    issue_checks   = failed_checks + doubt_checks

                    matched_txt = (
                        "Matched: " + ", ".join(c["attribute"] for c in passed_checks) + ". "
                        if passed_checks else ""
                    )
                    issues_txt = (
                        "Issues: " + ", ".join(c["attribute"] for c in issue_checks) + ". "
                        if issue_checks else ""
                    )

                    if ai_status == "approved":
                        default_msg = (
                            f"Hi {post['influencer_name']}, great work! Your post meets all "
                            f"campaign requirements. {matched_txt}"
                        )
                    else:
                        default_msg = (
                            f"Hi {post['influencer_name']}, please review the following before "
                            f"reposting. {issues_txt}{matched_txt}"
                        )

                    st.session_state[feedback_key] = default_msg.strip()

                dec_col1, dec_col2 = st.columns([1, 2])
                with dec_col1:
                    verdict = st.radio(
                        "Your Decision",
                        options=["approve", "reject"],
                        index=default_idx,
                        key=f"v_{post['post_id']}",
                        horizontal=True,
                        format_func=lambda x: "✅ Approve" if x == "approve" else "❌ Reject",
                    )
                with dec_col2:
                    feedback = st.text_area(
                        "Message to influencer (editable)",
                        key=feedback_key,
                        height=90,
                        label_visibility="collapsed",
                    )

                decisions[post["post_id"]] = {
                    "verdict":   verdict,
                    "feedback":  feedback,
                    "influencer": post["influencer_name"],
                    "ai_status": ai_status,
                }

    # ── Submit bar ────────────────────────────────────────────────────────
    st.markdown("---")

    # Live tally (always count ALL posts, not just filtered view)
    all_decisions_count = len(hitl_posts)
    will_approve = sum(
        1 for p in hitl_posts
        if decisions.get(p["post_id"], {}).get("verdict", "approve" if p["ai_status"] == "approved" else "reject") == "approve"
    )
    will_reject   = all_decisions_count - will_approve
    overrides     = sum(
        1 for p in hitl_posts
        if p["post_id"] in decisions and (
            (decisions[p["post_id"]]["verdict"] == "reject" and p["ai_status"] == "approved") or
            (decisions[p["post_id"]]["verdict"] == "approve" and p["ai_status"] != "approved")
        )
    )

    sb1, sb2, sb3, sb4 = st.columns([1, 1, 1, 2])
    sb1.metric("Will Approve", will_approve)
    sb2.metric("Will Reject",  will_reject)
    sb3.metric("Your Overrides", overrides)

    with sb4:
        if st.button(
            f"✅ Finalize — Approve {will_approve}  ·  Reject {will_reject}",
            type="primary", use_container_width=True,
        ):
            for p in hitl_posts:
                post_id = p["post_id"]
                dec = decisions.get(post_id)
                if dec is None:
                    # Post not visible in current filter — use default based on AI status
                    default_verdict = "approve" if p["ai_status"] == "approved" else "reject"
                    dec = {
                        "verdict": default_verdict, "feedback": "",
                        "influencer": p["influencer_name"], "ai_status": p["ai_status"],
                    }
                final = "approved" if dec["verdict"] == "approve" else "rejected"
                save_human_decisions(post_id, [dec], final)

            st.session_state.phase = "results"
            st.rerun()

    if st.button("← Back to Dashboard", use_container_width=True):
        st.session_state.phase = "dashboard"
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════
# PHASE: RESULTS — Final per-campaign breakdown
# ══════════════════════════════════════════════════════════════════════════
elif st.session_state.phase == "results":
    st.title("📊 Validation Results")

    # Gather finalized posts
    finalized = []
    for campaign in all_campaigns:
        for p in get_posts(campaign["id"]):
            if p["status"] in ("approved", "rejected"):
                finalized.append({**p, "campaign_name": campaign["name"], "brand": campaign["brand"]})

    approved_all = [p for p in finalized if p["status"] == "approved"]
    rejected_all = [p for p in finalized if p["status"] == "rejected"]

    # Human overrides
    overrides = sum(
        1 for p in finalized
        if p.get("human_decisions") and p["human_decisions"] and
        p["human_decisions"][0].get("ai_status") and (
            (p["status"] == "approved" and p["human_decisions"][0]["ai_status"] != "approved") or
            (p["status"] == "rejected" and p["human_decisions"][0]["ai_status"] == "approved")
        )
    )

    # Top metrics
    rm1, rm2, rm3, rm4 = st.columns(4)
    rm1.metric("Total Reviewed", len(finalized))
    rm2.metric("✅ Approved",    len(approved_all))
    rm3.metric("❌ Rejected",    len(rejected_all))
    rm4.metric("Human Overrides", overrides)

    # ── Feedback Report Table ─────────────────────────────────────────────
    st.subheader("📋 Decision & Feedback Report")
    table_rows = []
    for p in finalized:
        ai_rep    = p.get("ai_report") or {}
        checks    = ai_rep.get("checks", [])
        hd        = (p.get("human_decisions") or [{}])[0]
        ai_status = hd.get("ai_status", "—")
        override  = (
            (p["status"] == "approved" and ai_status not in ("approved",)) or
            (p["status"] == "rejected" and ai_status == "approved")
        )
        table_rows.append({
            "Influencer":     p["influencer_name"],
            "Campaign":       p.get("campaign_name", ""),
            "AI Decision":    ai_status.upper() if ai_status != "—" else "—",
            "Human Decision": p["status"].upper(),
            "Override":       "⚠️ YES" if override else "—",
            "Checks (P/F/D)": (
                f"{sum(1 for c in checks if c['status']=='pass')}/"
                f"{sum(1 for c in checks if c['status']=='fail')}/"
                f"{sum(1 for c in checks if c['status']=='doubt')}"
            ) if checks else "—",
            "Feedback Sent":  hd.get("feedback", "") or "—",
        })

    if table_rows:
        st.dataframe(table_rows, use_container_width=True, hide_index=True)
    else:
        st.info("No finalized decisions yet.")

    st.markdown("---")

    # Per-campaign tabs
    campaigns_with_data = [c for c in all_campaigns if get_posts(c["id"])]
    tabs = st.tabs([f"{c['brand']} — {c['name']}" for c in campaigns_with_data])

    for tab, campaign in zip(tabs, campaigns_with_data):
        with tab:
            posts    = get_posts(campaign["id"])
            approved = [p for p in posts if p["status"] == "approved"]
            rejected = [p for p in posts if p["status"] == "rejected"]
            pending  = [p for p in posts if p["status"] in ("pending", "needs_review")]

            tc1, tc2, tc3, tc4 = st.columns(4)
            tc1.metric("Total",    len(posts))
            tc2.metric("Approved", len(approved))
            tc3.metric("Rejected", len(rejected))
            tc4.metric("Pending",  len(pending))

            if approved:
                st.markdown("#### ✅ Approved")
                for p in approved:
                    with st.container(border=True):
                        a1, a2 = st.columns([4, 1])
                        with a1:
                            decided = "👤 Human" if p.get("human_decisions") else "🤖 AI"
                            st.markdown(f"**{p['influencer_name']}** — {decided}")
                            if p.get("ai_report"):
                                checks = p["ai_report"].get("checks", [])
                                passed = sum(1 for c in checks if c["status"] == "pass")
                                st.caption(f"{passed}/{len(checks)} checks passed · {p['ai_report'].get('summary','')}")
                            if p.get("human_decisions") and p["human_decisions"][0].get("feedback"):
                                st.caption(f"💬 {p['human_decisions'][0]['feedback']}")
                        with a2:
                            post_image(p["image_path"], width=80)

            if rejected:
                st.markdown("#### ❌ Rejected")
                for p in rejected:
                    with st.container(border=True):
                        r1, r2 = st.columns([4, 1])
                        with r1:
                            st.markdown(f"**{p['influencer_name']}**")
                            if p.get("ai_report"):
                                st.caption(p["ai_report"].get("summary", ""))
                            if p.get("human_decisions") and p["human_decisions"][0].get("feedback"):
                                st.caption(f"💬 Feedback sent: _{p['human_decisions'][0]['feedback']}_")
                        with r2:
                            post_image(p["image_path"], width=80)

            if pending:
                st.markdown("#### ⏳ Still Pending")
                for p in pending:
                    st.markdown(f"- **{p['influencer_name']}** · `{p['status']}`")

    st.markdown("---")
    if st.button("← Back to Dashboard", type="primary", use_container_width=True):
        st.session_state.phase = "dashboard"
        st.rerun()
