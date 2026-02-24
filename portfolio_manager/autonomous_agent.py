"""
Autonomous Portfolio Agent

This module provides utilities for running the portfolio agent in
autonomous (non-conversational) mode by providing a properly structured
prompt with all required profile information.

The root_agent from agent.py is used directly, but the initial message
is crafted to skip the conversational profile collection phase.
"""

# We use the root_agent directly since agents can only have one parent
# The autonomous behavior is achieved through the prompt structure
from .agent import root_agent

# Export
__all__ = ["root_agent"]
