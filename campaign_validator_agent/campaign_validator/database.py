"""SQLite database for campaigns and influencer posts."""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "campaign.db"
IMAGES_DIR = Path(__file__).parent.parent / "images"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT NOT NULL,
            requirements TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER NOT NULL,
            influencer_name TEXT NOT NULL,
            image_path TEXT,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            ai_report TEXT,
            human_decisions TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
        );
    """)
    conn.commit()
    conn.close()


def seed_data():
    conn = get_db()
    if conn.execute("SELECT COUNT(*) FROM campaigns").fetchone()[0] > 0:
        conn.close()
        return

    # ── Campaign 1: Coca-Cola Summer Vibes ────────────────────────────────
    conn.execute(
        "INSERT INTO campaigns (name, brand, requirements) VALUES (?, ?, ?)",
        (
            "Coca-Cola Summer Vibes 2026",
            "Coca-Cola",
            (
                "We are launching the Coca-Cola Summer Vibes 2026 campaign to celebrate "
                "the joy of summer with Coca-Cola. Every influencer post must show the "
                "influencer actively enjoying a Coca-Cola product — either drinking from "
                "a bottle or can, or holding it prominently. The Coca-Cola branding should "
                "be front and center: we want the logo clearly readable on the product, and "
                "ideally the influencer wearing Coca-Cola branded clothing or accessories "
                "like a t-shirt, cap, or wristband. The setting must feel summery and "
                "energetic — think beaches, pool parties, BBQs, outdoor festivals, or "
                "sunlit cityscapes. The overall mood should radiate fun, happiness, and "
                "togetherness. In the caption, the influencer should mention Coca-Cola by "
                "name and include the campaign hashtag #CocaColaSummer. We want the post "
                "to feel authentic and not overly staged."
            ),
        ),
    )

    coke_posts = [
        (
            1, "Sarah Chen", "coke_sarah.jpg",
            "Sarah posted an image at a sunny beach party where she is smiling and "
            "drinking from a classic Coca-Cola glass bottle. She is wearing a bright "
            "red Coca-Cola branded t-shirt with the logo printed across the front. "
            "The Coca-Cola logo is clearly visible on both the bottle and her shirt. "
            "The background shows ocean waves, palm trees, and friends playing volleyball. "
            "Her caption reads: 'Nothing beats a cold Coca-Cola on a hot summer day! "
            "Beach vibes and good times #CocaColaSummer #Refreshing #SummerVibes'"
        ),
        (
            1, "Mike Torres", "coke_mike.jpg",
            "Mike shared a photo of himself sitting on a park bench on a cloudy afternoon. "
            "He is holding a Pepsi can and taking a sip from it. He is wearing a plain "
            "grey hoodie with no branding of any kind. The park behind him has green "
            "trees and a jogger in the distance. There are no Coca-Cola products, logos, "
            "or branding anywhere in the image. His caption reads: 'Chilling with my "
            "favorite drink at the park today! Love this refreshing taste #ParkLife "
            "#ChillVibes' — notably, he does not mention Coca-Cola or use the campaign hashtag."
        ),
    ]

    # ── Campaign 2: Nike Just Move Fitness ────────────────────────────────
    conn.execute(
        "INSERT INTO campaigns (name, brand, requirements) VALUES (?, ?, ?)",
        (
            "Nike Just Move 2026",
            "Nike",
            (
                "The Nike Just Move 2026 campaign is about inspiring everyday people to "
                "get active and embrace movement in any form. Every influencer post must "
                "show the influencer actively engaged in some form of exercise or sport — "
                "running, yoga, gym training, cycling, hiking, or any physical activity. "
                "The influencer must be wearing at least one visible Nike product such as "
                "Nike shoes, a Nike top, shorts, or headband, with the Nike Swoosh logo "
                "clearly visible somewhere in the image. The setting should be active and "
                "dynamic — outdoors, at a gym, on a trail, or in a sports facility. The "
                "overall mood should convey energy, determination, and empowerment. In the "
                "caption, the influencer must mention Nike by name and include the campaign "
                "hashtag #JustMove. The post should feel motivational and authentic, not "
                "like a product catalog."
            ),
        ),
    )

    nike_posts = [
        (
            2, "Emma Rodriguez", "nike_emma.jpg",
            "Emma posted a photo from her morning trail run in the mountains. She is "
            "mid-stride on a dirt path surrounded by pine trees and morning mist. She "
            "is wearing bright orange Nike running shoes with the Swoosh clearly visible, "
            "a black Nike Dri-FIT tank top with a small white Swoosh on the chest, and "
            "grey running leggings. Her expression is focused and determined. The scenery "
            "is breathtaking with rolling green hills in the background. Her caption reads: "
            "'5am alarm, zero regrets. These Nike Pegasus shoes make every mile feel like "
            "the first. Get out there and move! #JustMove #TrailRunning #NikeRunning'"
        ),
        (
            2, "Jake Williams", "nike_jake.png",
            "Jake shared a mirror selfie from a fancy coffee shop. He is wearing a "
            "plain white dress shirt with rolled-up sleeves and dark jeans. He is holding "
            "a latte in one hand and his phone in the other. There is no athletic wear, "
            "no Nike products, and no sports equipment visible anywhere in the image. The "
            "background shows espresso machines, pastries in a display case, and other "
            "customers sitting at tables. His caption reads: 'Morning fuel before a big "
            "day! Love this cozy spot #CoffeeTime #MondayMotivation #Lifestyle' — he "
            "does not mention Nike or use the campaign hashtag."
        ),
    ]

    # ── Campaign 3: L'Oreal Paris Glow Up ─────────────────────────────────
    conn.execute(
        "INSERT INTO campaigns (name, brand, requirements) VALUES (?, ?, ?)",
        (
            "L'Oreal Paris Glow Up 2026",
            "L'Oreal Paris",
            (
                "The L'Oreal Paris Glow Up 2026 campaign celebrates self-confidence and "
                "the power of a great skincare routine. Every influencer post must feature "
                "at least one L'Oreal Paris product visibly in the image — whether it is "
                "a serum bottle, moisturizer jar, or makeup item — with the L'Oreal Paris "
                "logo or product label readable. The influencer should appear with glowing, "
                "healthy-looking skin, ideally in a close-up or beauty-style shot that "
                "highlights their complexion. The setting should feel clean, bright, and "
                "elegant — think bathroom vanity, well-lit bedroom, or professional studio. "
                "Avoid cluttered or dark backgrounds. In the caption, the influencer must "
                "mention L'Oreal Paris by name and include the hashtag #GlowUpWithLoreal. "
                "The tone should feel empowering and aspirational, conveying 'Because "
                "You're Worth It' energy. The post must not feature competitor beauty brands."
            ),
        ),
    )

    loreal_posts = [
        (
            3, "Priya Patel", "loreal_priya.jpg",
            "Priya posted a close-up beauty shot taken in a bright, minimalist bathroom. "
            "She is holding a L'Oreal Paris Revitalift serum bottle next to her face, "
            "with the gold L'Oreal Paris logo clearly readable on the product label. Her "
            "skin looks radiant and dewy, and she is smiling confidently at the camera. "
            "The background shows a clean white marble countertop with soft natural light "
            "coming from a window. Her caption reads: 'My morning glow secret? This "
            "L'Oreal Paris Revitalift serum has transformed my skin in just 2 weeks. "
            "Because we are all worth it! #GlowUpWithLoreal #Skincare #MorningRoutine'"
        ),
        (
            3, "Aisha Khan", "loreal_aisha.jpg",
            "Aisha shared a dimly lit selfie taken in her car at night. The photo is "
            "slightly blurry and her face is partially in shadow. She is not holding any "
            "beauty products, and no L'Oreal items are visible anywhere in the frame. She "
            "appears to be wearing heavy makeup but no specific brand can be identified. A "
            "Maybelline mascara tube is sitting in the cupholder beside her, clearly showing "
            "the Maybelline logo. The background is dark with some streetlight bokeh. Her "
            "caption reads: 'Night out glam! Feeling cute tonight #Selfie #NightOut "
            "#MakeupLook' — she does not mention L'Oreal Paris or use the campaign hashtag."
        ),
        (
            3, "Lucas Chen", "loreal_lucas.jpg",
            "Lucas posted a well-lit photo from his bathroom vanity. He is applying a "
            "L'Oreal Paris Men Expert moisturizer, with the product held at chest height "
            "showing the L'Oreal Paris branding on the tube. However, the background is "
            "extremely cluttered — towels piled up, toothbrushes scattered, and several "
            "other random products from different brands visible on the counter. The "
            "lighting is good and his skin looks healthy. His caption reads: 'Skincare "
            "isn't just for the ladies! L'Oreal Paris Men Expert keeps my skin fresh all "
            "day. #GlowUpWithLoreal #MensSkincare #SelfCare'"
        ),
    ]

    all_posts = coke_posts + nike_posts + loreal_posts
    for campaign_id, name, img, desc in all_posts:
        conn.execute(
            "INSERT INTO posts (campaign_id, influencer_name, image_path, description) VALUES (?, ?, ?, ?)",
            (campaign_id, name, img, desc),
        )

    conn.commit()
    conn.close()

    # Write image generation guide (only if not already present)
    desc_path = IMAGES_DIR / "IMAGE_DESCRIPTIONS.txt"
    desc_path.parent.mkdir(exist_ok=True)
    if not desc_path.exists():
        with open(desc_path, "w") as f:
            f.write("=== IMAGE GENERATION GUIDE ===\n")
            f.write("Generate these images and save them with the filenames below in images/\n\n")
            for campaign_id, name, img, desc in all_posts:
                f.write(f"--- {img} ({name}) ---\n{desc}\n\n")


# ── Query helpers ─────────────────────────────────────────────────────────

def get_campaigns() -> list[dict]:
    conn = get_db()
    rows = conn.execute("SELECT * FROM campaigns ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_campaign(campaign_id: int) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_posts(campaign_id: int) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM posts WHERE campaign_id = ? ORDER BY id", (campaign_id,)
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        if d["ai_report"]:
            d["ai_report"] = json.loads(d["ai_report"])
        if d["human_decisions"]:
            d["human_decisions"] = json.loads(d["human_decisions"])
        result.append(d)
    return result


def update_post_report(post_id: int, status: str, ai_report: dict):
    conn = get_db()
    conn.execute(
        "UPDATE posts SET status = ?, ai_report = ? WHERE id = ?",
        (status, json.dumps(ai_report), post_id),
    )
    conn.commit()
    conn.close()


def save_human_decisions(post_id: int, decisions: list[dict], final_status: str):
    conn = get_db()
    conn.execute(
        "UPDATE posts SET status = ?, human_decisions = ? WHERE id = ?",
        (final_status, json.dumps(decisions), post_id),
    )
    conn.commit()
    conn.close()

def reset_all_posts(campaign_id: int):
    conn = get_db()
    conn.execute(
        "UPDATE posts SET status = 'pending', ai_report = NULL, human_decisions = NULL WHERE campaign_id = ?",
        (campaign_id,),
    )
    conn.commit()
    conn.close()


def reset_all_campaigns():
    conn = get_db()
    conn.execute("UPDATE posts SET status = 'pending', ai_report = NULL, human_decisions = NULL")
    conn.commit()
    conn.close()


def add_campaign(name: str, brand: str, requirements: str) -> int:
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO campaigns (name, brand, requirements) VALUES (?, ?, ?)",
        (name, brand, requirements),
    )
    campaign_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return campaign_id


def update_campaign(campaign_id: int, name: str, brand: str, requirements: str):
    conn = get_db()
    conn.execute(
        "UPDATE campaigns SET name = ?, brand = ?, requirements = ? WHERE id = ?",
        (name, brand, requirements, campaign_id),
    )
    conn.commit()
    conn.close()


def add_post(campaign_id: int, influencer_name: str, image_path: str, description: str) -> int:
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO posts (campaign_id, influencer_name, image_path, description) VALUES (?, ?, ?, ?)",
        (campaign_id, influencer_name, image_path, description),
    )
    post_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return post_id


def delete_post(post_id: int):
    conn = get_db()
    conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
