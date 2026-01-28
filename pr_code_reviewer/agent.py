from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from .sub_agents.security_auditor import security_auditor
from .sub_agents.style_checker import style_checker
from .sub_agents.performance_analyzer import performance_analyzer
from .sub_agents.logic_verifier import logic_verifier
from .sub_agents.docs_reviewer import docs_reviewer

GEMINI_MODEL = "gemini-2.0-flash"

# --- Synthesizer Agent ---
review_synthesizer = LlmAgent(
    name="review_synthesizer",
    model=GEMINI_MODEL,
    instruction="""You are the Lead Code Reviewer and Decision Engine.
Your goal is to aggregate reviews from specialized agents and make a text-based decision on the PR.

Inputs from Sub-Agents:
1. Security Report: {security_report}
2. Style Report: {style_report}
3. Performance Report: {performance_report}
4. Logic Report: {logic_report}
5. Docs Report: {docs_report}

Instructions:
1. Read the reports from all agents.
2. Apply the following strict Decision Rules:
   - IF any High Severity Security Issue is found -> Decision: REQUEST_CHANGES (Block)
   - IF Logic/Correctness fail -> Decision: REQUEST_CHANGES
   - IF only Style/Docs issues -> Decision: COMMENT (or APPROVE with nits)
   - IF no issues -> Decision: APPROVE

3. Output a JSON object with the final verdict and summary. 

CRITICAL: In your "summary_markdown", you MUST preserve the specific feedback provided by the sub-agents. 
Do not summarize them into generic statements.
Copy the "**File:** ... **Line:** ... **Fix:** ..." blocks exactly as they are in the sub-reports so the user can find the code easily.

**Output Format (JSON ONLY):**
{
  "decision": "APPROVE" | "REQUEST_CHANGES" | "COMMENT",
  "summary_markdown": "### PR Review Summary... (your formatted markdown here)",
  "checks": {
    "security": "success" | "failure",
    "style": "success" | "failure",
    "performance": "success" | "failure",
    "logic": "success" | "failure"
  }
}
""",
    output_key="final_review_decision"
)

# --- Parallel Orchestrator ---
parallel_review_swarm = ParallelAgent(
    name="parallel_review_swarm",
    sub_agents=[
        security_auditor, 
        style_checker, 
        performance_analyzer, 
        logic_verifier, 
        docs_reviewer
    ],
    description="Runs all code review specialists in parallel."
)

# --- Root Agent ---
root_agent = SequentialAgent(
    name="pr_code_review_pipeline",
    sub_agents=[parallel_review_swarm, review_synthesizer],
    description="Orchestrates the parallel code review and final synthesis."
)
