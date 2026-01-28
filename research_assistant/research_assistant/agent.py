from google.adk.agents import SequentialAgent
from .sub_agents import (
    # Universal Multi-Mode Agents
    intent_detector_agent,
    data_processor_agent,
    analyzer_agent,
    extractor_agent,
    report_generator_agent,
)


# Create the Universal Multi-Mode Research Assistant
# Handles: Research Analysis, Literature Review, Competitive Analysis
# All in ONE sequential pipeline that adapts based on input

# Named 'root_agent' for ADK tools compatibility as per official documentation
root_agent = SequentialAgent(
    name="UniversalResearchAssistant",
    description="""A universal multi-mode research assistant that automatically adapts to:

    🔬 MODE 1: RESEARCH ASSISTANT
       - Single document + specific question
       - Pipeline: Detect → Process → Search → Extract Citations → Summarize
       
    📚 MODE 2: LITERATURE REVIEW  
       - Multiple sources or comprehensive topic analysis
       - Pipeline: Detect → Gather → Categorize → Analyze Themes → Synthesize
       
    🏆 MODE 3: COMPETITIVE ANALYSIS
       - Company/product/market comparison
       - Pipeline: Detect → Gather Data → Compare → Score → Report
    
    The system automatically detects which mode to use based on input!
    
    Universal Pipeline Flow (5 Agents):
    1. IntentDetectorAgent → Detects analysis mode → output_key="detected_intent"
    2. DataProcessorAgent → Adapts processing → output_key="processed_data"
    3. AnalyzerAgent → Search/Categorize/Compare → output_key="analysis_results"
    4. ExtractorAgent → Extract/Synthesize/Score → output_key="extracted_output"
    5. ReportGeneratorAgent → Final report → output_key="final_report"
    """,
    
    # Universal Pipeline - adapts to detected mode
    sub_agents=[
        intent_detector_agent,    # Step 1: Detect mode (Research/Literature/Competitive)
        data_processor_agent,     # Step 2: Process data based on mode
        analyzer_agent,           # Step 3: Analyze (Search/Categorize/Compare)
        extractor_agent,          # Step 4: Extract (Citations/Synthesis/Scores)
        report_generator_agent    # Step 5: Generate final report
    ]
)

# Also export as research_assistant for backward compatibility
research_assistant = root_agent
