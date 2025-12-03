"""Centralized LLM prompts used across the research agents.

Each logical prompt (or closely related prompt family) has its own module so
that:
- The full text lives in one place
- It is easy to see where the prompt is used
- Prompts can be iterated on without hunting through node/service code
"""

from .web_search import (
    build_web_search_instructions,
    build_query_generation_instructions,
    build_query_generation_prompt
)

__all__ = [
    "build_web_search_instructions",
    "build_query_generation_instructions",
    "build_query_generation_prompt",
]


