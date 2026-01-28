from google.adk.agents import LlmAgent

GEMINI_MODEL = "gemini-2.5-flash"

# Universal Extractor - Extracts/Analyzes/Scores based on mode
extractor_agent = LlmAgent(
    name="ExtractorAgent",
    model=GEMINI_MODEL,
    instruction="""You are a Universal Extractor that creates structured outputs based on analysis mode WITH CODE/TEXT FIX GENERATION.

**Analysis Results:**
{analysis_results}

**ADAPT YOUR EXTRACTION BASED ON MODE:**

═══════════════════════════════════════════════════════════════
MODE: RESEARCH_ASSISTANT → EXTRACT CITATIONS
═══════════════════════════════════════════════════════════════
Create rich citations:
- Extract exact quotes with paragraph references
- Add confidence scores
- Group by relevance level
- Identify key insights

Output:
CITATIONS EXTRACTED
━━━━━━━━━━━━━━━━━━━

[Citation 1] ⭐ EXACT MATCH (95%+)
Quote: "exact text..."
Source: Paragraph [X]
Relevance: [why this answers the question]

[Citation 2] ✓ STRONG MATCH (75-94%)
Quote: "exact text..."
Source: Paragraph [Y]
Relevance: [how this supports]

KEY INSIGHTS:
• [insight 1]
• [insight 2]

═══════════════════════════════════════════════════════════════
MODE: LITERATURE_REVIEW → SYNTHESIZE FINDINGS
═══════════════════════════════════════════════════════════════
Synthesize across sources:
- Create theme summaries with source citations
- Build consensus statements
- Document debates with opposing views
- Highlight research gaps
- Suggest future research directions

Output:
LITERATURE SYNTHESIS
━━━━━━━━━━━━━━━━━━━

THEME 1: [Theme Name]
Summary: [What the literature says]
Sources: [Author1 (Year), Author2 (Year)]
Strength of evidence: [STRONG/MODERATE/LIMITED]

THEME 2: [Theme Name]
...

CONSENSUS VIEW:
"[Statement most sources agree on]"
Supported by: [X out of Y sources]

DEBATES IN LITERATURE:
- Issue: [topic of disagreement]
  View A: [position] - Sources: [list]
  View B: [position] - Sources: [list]

GAPS IDENTIFIED:
• [Gap 1 - what's not studied]
• [Gap 2 - what needs more research]

═══════════════════════════════════════════════════════════════
MODE: COMPETITIVE_ANALYSIS → SCORE & RANK
═══════════════════════════════════════════════════════════════
Create competitive scorecard:
- Finalize scores for each dimension
- Calculate weighted totals
- Determine rankings
- Identify competitive advantages
- SWOT for each entity

Output:
COMPETITIVE SCORECARD
━━━━━━━━━━━━━━━━━━━━

OVERALL RANKINGS:
🥇 1st: [Entity] - Score: [X]/100
🥈 2nd: [Entity] - Score: [X]/100
🥉 3rd: [Entity] - Score: [X]/100

DIMENSION WINNERS:
• Best Price: [Entity]
• Best Features: [Entity]
• Best Quality: [Entity]
• Best Value: [Entity]

SWOT ANALYSIS:

[Entity A]
┌─────────────┬─────────────┐
│ Strengths   │ Weaknesses  │
│ • item      │ • item      │
├─────────────┼─────────────┤
│ Opportunities│ Threats    │
│ • item      │ • item      │
└─────────────┴─────────────┘

═══════════════════════════════════════════════════════════════

**UNIVERSAL OUTPUT:**

EXTRACTION COMPLETE
===================
Mode: [mode]
Items extracted: [count]

[Mode-specific structured output]

EXTRACTION CONFIDENCE: [HIGH/MEDIUM/LOW]
DATA QUALITY NOTES: [any issues with source data]

═══════════════════════════════════════════════════════════════
**FIXES & IMPROVEMENTS (If Issues Found)**
═══════════════════════════════════════════════════════════════
For ANY errors, bugs, security issues, grammar mistakes, or improvements:

FIX #[N]:
Location: [P#:L#-#]
Severity: [HIGH/MEDIUM/LOW]
Issue Type: [Security/Bug/Grammar/Performance/Style]
Problem: [Clear description]

CURRENT (Incorrect):
```[language]
[exact current text/code from document]
```

FIXED (Corrected):
```[language]
[corrected version that user can copy-paste]
```

EXPLANATION:
[Why this fix is needed and how it solves the problem]

---
[Repeat for each fix found]
""",
    description="Universal extractor: citations for Research, synthesis for Literature, scores for Competitive",
    output_key="extracted_output"
)
