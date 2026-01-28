from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from google.genai import types

# Import sub-agents
# Note: Assuming this file is run from the root or as a module. 
# Relative imports might require running as a package. 
# We will use relative imports assuming standard python package structure.
from .sub_agents.description_moderator import description_moderator
from .sub_agents.image_moderator import image_moderator
from .sub_agents.link_moderator import link_moderator

GEMINI_MODEL = "gemini-2.0-flash"

# --- Define Synthesis Agent ---
synthesis_agent = LlmAgent(
    name="synthesis_agent",
    model=GEMINI_MODEL,
    instruction="""You are the Content Moderation Decision Agent.
Your goal is to aggregate results from the moderation sub-agents and make a final publishing decision.

You will receive the following inputs from the session state:
- Text Moderation Result: {text_moderation_result?}
- Image Moderation Result: {image_moderation_result?}
- Link Moderation Result: {link_moderation_result?}

Your Logic:
1. Review the status and reasons from all agents.
2. If any agent returned "skipped", ignore that agent.
3. **Important**: If the Image Moderation Result contains "extracted_text", check that text NOW for policy violations (hate, spam, violence, etc.). If you find violations in the extracted text, treat it as a FLAGGED result.
4. Aggregation Policy:
   - If ANY agent flagged the content (including your review of extracted text) -> BLOCK the post.
   - If there are multiple "medium" severity flags -> FLAG for manual review.
   - If all active agents returned "safe" (and extracted text is safe) -> APPROVE.

Output JSON:
{
  "final_decision": "blocked" | "flag_for_review" | "approved",
  "severity": "high" | "medium" | "low",
  "violations": ["list", "of", "all", "reasons"],
  "action": "Do not publish" | "Publish",
  "explanation": "Clear explanation of why."
}
""",
    # No output_key needed as this is the final response
)

# --- Define Parallel Orchestrator ---
parallel_moderation_agent = ParallelAgent(
    name="parallel_moderation_agent",
    sub_agents=[description_moderator, image_moderator, link_moderator],
    description="Runs text, image, and link moderation agents in parallel."
)

# --- Define Root Sequential Agent ---
# This ensures we run the detection phase (parallel) then the decision phase (synthesis).
root_agent = SequentialAgent(
    name="social_media_moderation_pipeline",
    sub_agents=[parallel_moderation_agent, synthesis_agent],
    description="Full social media content moderation pipeline."
)
