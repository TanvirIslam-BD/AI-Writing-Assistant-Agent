"""
AI Writing Assistant Package

A comprehensive AI-powered writing assistant that helps improve text quality
through grammar correction, sentence rewriting, tone adjustment, and vocabulary enhancement.
"""

__version__ = "1.0.0"
__author__ = "AI Writing Assistant Team"
__description__ = "AI-powered writing improvement tools"

from .agent import AIWritingAgent, WritingTool
from .tools import (
    GrammarCorrector,
    SentenceRewriter,
    ToneAdjuster,
    VocabularyEnhancer
)

__all__ = [
    'AIWritingAgent',
    'WritingTool',
    'GrammarCorrector',
    'SentenceRewriter',
    'ToneAdjuster',
    'VocabularyEnhancer'
]