"""
LLM prompts for debt collection conversations.

This module provides:
- Stage-specific system prompts (pre-delinquency, early, late)
- Post-call extraction prompt for CallExtraction schema
"""

from .debt_collection import (
    get_system_prompt,
    PRE_DELINQUENCY_PROMPT,
    EARLY_DELINQUENCY_PROMPT,
    LATE_DELINQUENCY_PROMPT,
)
from .extraction import EXTRACTION_PROMPT

__all__ = [
    "get_system_prompt",
    "PRE_DELINQUENCY_PROMPT",
    "EARLY_DELINQUENCY_PROMPT",
    "LATE_DELINQUENCY_PROMPT",
    "EXTRACTION_PROMPT",
]
