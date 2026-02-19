"""Autonomous campaign validation agent — pure LLM reasoning.

Two-phase pipeline, both powered entirely by LLM (no regex, no tools):

Phase 1 — Attribute Extraction:
    An LLM agent reads the campaign requirements paragraph and extracts
    the specific, checkable attributes relevant to validating an image post.

Phase 2 — Post Validation:
    For each post, an LLM agent receives:
      - The extracted attributes
      - The post description (natural paragraph that includes caption)
      - The post image
    It autonomously reasons about compliance and returns a structured verdict.
"""

import json
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

from campaign_validator.config import GEMINI_MODEL
IMAGES_DIR = Path(__file__).parent.parent / "images"


# ── Phase 1: Extract checkable attributes from campaign requirements ──────

async def extract_attributes(requirements: str, brand: str) -> str | None:
    """LLM reads the campaign requirements paragraph and extracts key
    attributes that should be checked when validating an influencer post.

    Returns the extracted attributes as a plain text string (LLM-generated).
    This text is then fed into the validator agents as their checklist.
    """
    agent = LlmAgent(
        name="AttributeExtractor",
        model=GEMINI_MODEL,
        description="Extracts checkable validation attributes from campaign requirements.",
        instruction=(
            f"You are a campaign analyst for {brand}.\n\n"
            "Read the campaign requirements paragraph below. Your job is to extract "
            "every specific, independently-checkable attribute that a reviewer should "
            "verify when looking at an influencer's post (image + caption).\n\n"
            "Group them into two categories:\n"
            "VISUAL ATTRIBUTES — things to check in the image (product visibility, "
            "branding, clothing, setting, mood, etc.)\n"
            "CONTENT ATTRIBUTES — things to check in the caption/text (mentions, "
            "hashtags, tone, authenticity, etc.)\n\n"
            "Output a clean numbered list under each category. Be specific and "
            "actionable. Each attribute should be one clear thing to verify.\n"
            "Output ONLY the list, no preamble."
        ),
        output_key="extracted_attributes",
    )

    runner = InMemoryRunner(agent=agent, app_name="attribute_extractor")
    session = await runner.session_service.create_session(
        app_name="attribute_extractor", user_id="system"
    )

    message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=f"Extract checkable attributes from:\n\n{requirements}")],
    )

    result = None
    async for event in runner.run_async(
        user_id="system", session_id=session.id, new_message=message,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text and part.text.strip():
                    result = part.text.strip()

    return result


# ── Phase 2: Validate a single post ──────────────────────────────────────

async def validate_post(
    campaign_name: str,
    brand: str,
    attributes: str,
    influencer_name: str,
    description: str,
    image_path: str | None,
) -> dict | None:
    """LLM autonomously validates a post against the extracted attributes.

    The agent receives:
      - The extracted attributes checklist
      - The post description paragraph (includes caption context)
      - The post image (if available)

    It reasons freely and outputs a structured JSON verdict.
    """
    instruction = (
        f"You are an autonomous campaign compliance reviewer for {brand}.\n\n"
        f"CAMPAIGN: {campaign_name}\n\n"
        f"ATTRIBUTES TO CHECK:\n{attributes}\n\n"
        f"INFLUENCER: {influencer_name}\n"
        f"POST DESCRIPTION:\n{description}\n\n"
        "YOUR TASK:\n"
        "Carefully examine the image (if provided) and read the post description above. "
        "The description includes what the influencer posted and their caption. "
        "Evaluate the post against EVERY attribute listed above.\n\n"
        "For each attribute, reason about whether the post meets it, fails it, "
        "or is ambiguous. Be thorough and specific in your reasoning — cite "
        "exactly what you see or don't see.\n\n"
        "OUTPUT FORMAT — output ONLY valid JSON, no markdown fences:\n"
        'A JSON object with exactly three keys:\n'
        '- "checks": array of objects, each with "attribute" (string), '
        '"status" (string: "pass" or "fail" or "doubt"), '
        '"reasoning" (string: what you observed)\n'
        '- "overall_status": "approved" if ALL checks pass, '
        '"needs_review" if any are "doubt", "rejected" if any are "fail"\n'
        '- "summary": 1-2 sentence overall assessment of the post\n\n'
        "Be strict and honest. Output ONLY the JSON."
    )

    agent = LlmAgent(
        name=f"PostValidator_{influencer_name.replace(' ', '_')}",
        model=GEMINI_MODEL,
        description="Validates an influencer post against campaign attributes.",
        instruction=instruction,
        output_key="validation_result",
    )

    runner = InMemoryRunner(agent=agent, app_name="post_validator")
    session = await runner.session_service.create_session(
        app_name="post_validator", user_id="system"
    )

    # Build message parts — image + text
    parts = [
        types.Part.from_text(
            text=f"Validate this post by {influencer_name} for the {campaign_name} campaign."
        ),
    ]

    # Attach image if available
    if image_path:
        full_path = IMAGES_DIR / image_path
        if full_path.exists():
            image_bytes = full_path.read_bytes()
            ext = full_path.suffix.lower()
            mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}.get(ext, "image/jpeg")
            parts.append(types.Part.from_bytes(data=image_bytes, mime_type=mime))

    user_message = types.Content(role="user", parts=parts)

    result = None
    async for event in runner.run_async(
        user_id="system", session_id=session.id, new_message=user_message,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if not part.text:
                    continue
                text = _strip_code_fences(part.text.strip())
                try:
                    result = json.loads(text)
                except json.JSONDecodeError:
                    pass

    return result


# ── Batch validation ──────────────────────────────────────────────────────

async def validate_campaign_posts(campaign: dict, posts: list[dict]) -> list[dict]:
    """Full autonomous pipeline: extract attributes, then validate all posts.

    Phase 1: LLM extracts attributes from campaign requirements.
    Phase 2: For each post, LLM validates against those attributes.

    Returns list of {"post_id": int, "report": dict} results.
    """
    # Phase 1 — extract attributes once for the whole campaign
    attributes = await extract_attributes(campaign["requirements"], campaign["brand"])
    if not attributes:
        return []

    # Phase 2 — validate each post
    results = []
    for post in posts:
        report = await validate_post(
            campaign_name=campaign["name"],
            brand=campaign["brand"],
            attributes=attributes,
            influencer_name=post["influencer_name"],
            description=post["description"],
            image_path=post.get("image_path"),
        )
        results.append({
            "post_id": post["id"],
            "influencer_name": post["influencer_name"],
            "report": report,
            "attributes_used": attributes,
        })

    return results


def _strip_code_fences(text: str) -> str:
    if not text.startswith("```"):
        return text
    lines = text.split("\n")
    json_lines = []
    inside = False
    for line in lines:
        if line.startswith("```") and not inside:
            inside = True
            continue
        elif line.startswith("```") and inside:
            break
        elif inside:
            json_lines.append(line)
    return "\n".join(json_lines)
