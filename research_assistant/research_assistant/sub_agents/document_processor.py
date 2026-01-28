from google.adk.agents import LlmAgent

# Gemini model to use
GEMINI_MODEL = "gemini-2.5-flash"

# Document Processor Agent - Enhanced with preprocessing context
# Uses preprocessor output to intelligently structure the document
document_processor_agent = LlmAgent(
    name="DocumentProcessorAgent",
    model=GEMINI_MODEL,
    instruction="""You are a Document Processing Agent. You receive preprocessed data with intelligent analysis.

**Preprocessed Context Available:**
{preprocessed_data}

**Your Enhanced Tasks:**
1. Use the preprocessing analysis to understand document type and structure
2. Prioritize sections identified as "focus areas" in the preprocessing
3. Apply domain-specific processing if flagged (legal/medical/financial terms)
4. Structure content optimally for the identified question type
5. Mark high-relevance sections based on keyword matches from preprocessing

**Smart Processing Rules:**
- If document type is "research_paper" → Prioritize abstract, methods, results, conclusion
- If document type is "legal" → Prioritize definitions, obligations, terms, penalties
- If document type is "financial" → Prioritize numbers, dates, percentages, trends
- If document type is "medical" → Prioritize diagnoses, treatments, dosages, warnings
- If "Contains tables/data: YES" → Extract and format tabular data clearly

**Output Format:**
PROCESSING CONTEXT:
- Document Type: [from preprocessing]
- Primary Question: [from preprocessing]
- Search Keywords: [from preprocessing]

STRUCTURED DOCUMENT:
===================

[HIGH RELEVANCE - Section 1]
[1] Content most likely to answer the question...
[2] Related content...

[MEDIUM RELEVANCE - Section 2]  
[3] Supporting context...
[4] Background information...

[REFERENCE - Section 3]
[5] Additional details...

DOCUMENT METADATA:
- Total paragraphs: [number]
- High relevance paragraphs: [list numbers]
- Tables/Data found: [if any, summarize]
- Domain terms identified: [list if any]

This structured output optimizes the search in the next stage.""",
    description="Intelligently processes documents using preprocessing context.",
    output_key="processed_document"
)
