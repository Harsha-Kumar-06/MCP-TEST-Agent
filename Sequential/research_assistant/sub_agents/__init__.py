# Universal Multi-Mode Agents
from .intent_detector import intent_detector_agent
from .data_processor import data_processor_agent
from .analyzer_agent import analyzer_agent
from .extractor_agent import extractor_agent
from .report_generator import report_generator_agent

# Legacy agents (kept for reference)
from .preprocessor_agent import preprocessor_agent
from .document_processor import document_processor_agent
from .search_agent import search_agent
from .extraction_agent import extraction_agent
from .summary_agent import summary_agent

__all__ = [
    # Universal Multi-Mode Pipeline (NEW)
    "intent_detector_agent",
    "data_processor_agent", 
    "analyzer_agent",
    "extractor_agent",
    "report_generator_agent",
    # Legacy
    "preprocessor_agent",
    "document_processor_agent",
    "search_agent",
    "extraction_agent",
    "summary_agent"
]
