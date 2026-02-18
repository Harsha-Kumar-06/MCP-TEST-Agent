"""Sub-agents for specialized task handling."""

from .hr_agent import hr_agent
from .it_support_agent import it_support_agent
from .sales_agent import sales_agent
from .legal_agent import legal_agent
from .off_topic_agent import off_topic_agent

__all__ = [
    "hr_agent",
    "it_support_agent",
    "sales_agent",
    "legal_agent",
    "off_topic_agent",
]
