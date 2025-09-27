"""
LangChain Tools for AI Writing Assistant
Self-contained implementation of writing improvement tools
"""

from typing import Dict, Optional
from langchain_core.tools import tool
import re


# Grammar correction patterns and logic
GRAMMAR_PATTERNS = {
    # Common word confusions
    r'\btheir\b(?=\s+(?:going|coming|will|should|would|can|could))': 'they\'re',
    r'\bthere\b(?=\s+(?:car|house|dog|cat|friend))': 'their',
    r'\bthey\'re\b(?=\s+(?:car|house|dog|cat|friend))': 'their',
    r'\byour\b(?=\s+(?:going|coming|will|should|would|can|could))': 'you\'re',
    r'\byou\'re\b(?=\s+(?:car|house|dog|cat|friend|book))': 'your',
    r'\bits\b(?=\s+(?:going|coming|will|should|would|can|could))': 'it\'s',
    r'\bit\'s\b(?=\s+(?:car|house|dog|cat|friend|book|color))': 'its',
    # Double spaces
    r'\s{2,}': ' ',
    # Capitalization after sentence endings
    r'([.!?]\s+)([a-z])': lambda m: m.group(1) + m.group(2).upper(),
    # Missing periods at end
    r'([a-zA-Z])$': r'\1.',
}

# Sentence rewriting patterns
SENTENCE_PATTERNS = {
    r'\bdue to the fact that\b': 'because',
    r'\bin order to\b': 'to',
    r'\bat this point in time\b': 'now',
    r'\bfor the purpose of\b': 'for',
    r'\bin the event that\b': 'if',
    r'\bit is important to note that\b': '',
    r'\bof course\b': '',
}

# Vocabulary enhancement mappings
VOCABULARY_UPGRADES = {
    'good': 'excellent',
    'bad': 'poor',
    'big': 'substantial',
    'small': 'minimal',
    'nice': 'pleasant',
    'great': 'outstanding',
    'very': 'extremely',
    'really': 'remarkably',
    'quite': 'considerably',
    'pretty': 'rather',
    'thing': 'element',
    'stuff': 'material'
}

# Tone adjustment patterns
TONE_PATTERNS = {
    'formal': {
        'replacements': {
            r'\bokay\b': 'acceptable',
            r'\byeah\b': 'yes',
            r'\bgonna\b': 'going to',
            r'\bwanna\b': 'wish to',
            r'\bcool\b': 'satisfactory',
        },
        'style': 'formal and professional'
    },
    'casual': {
        'replacements': {
            r'\butilize\b': 'use',
            r'\bcommence\b': 'start',
            r'\bsubsequently\b': 'then',
            r'\bfurthermore\b': 'also',
        },
        'style': 'casual and conversational'
    },
    'professional': {
        'replacements': {
            r'\btotally\b': 'completely',
            r'\babsolutely\b': 'certainly',
            r'\bamazing\b': 'excellent',
        },
        'style': 'professional and business-like'
    },
    'friendly': {
        'replacements': {
            r'\bdemand\b': 'ask for',
            r'\brequire\b': 'need',
            r'\bmust\b': 'should',
        },
        'style': 'friendly and approachable'
    }
}


@tool
def grammar_correction_tool(text: str) -> str:
    """
    Fixes grammar, spelling, and punctuation errors in the provided text.

    Args:
        text: The text to be corrected

    Returns:
        str: The text with grammar corrections applied
    """
    try:
        result = text
        for pattern, replacement in GRAMMAR_PATTERNS.items():
            if callable(replacement):
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
            else:
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result.strip()
    except Exception as e:
        return f"Error in grammar correction: {str(e)}"


@tool
def sentence_rewriting_tool(text: str) -> str:
    """
    Improves sentence structure and clarity by rewriting complex or wordy sentences.

    Args:
        text: The text to be rewritten

    Returns:
        str: The text with improved sentence structure
    """
    try:
        result = text
        for pattern, replacement in SENTENCE_PATTERNS.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        # Clean up extra spaces
        result = re.sub(r'\s+', ' ', result)
        return result.strip()
    except Exception as e:
        return f"Error in sentence rewriting: {str(e)}"


@tool
def vocabulary_enhancement_tool(text: str) -> str:
    """
    Replaces basic words with more sophisticated alternatives to enhance vocabulary.

    Args:
        text: The text to enhance

    Returns:
        str: The text with enhanced vocabulary
    """
    try:
        words = text.split()
        enhanced_words = []
        for word in words:
            # Remove punctuation for lookup
            clean_word = re.sub(r'[^\w]', '', word.lower())
            if clean_word in VOCABULARY_UPGRADES:
                # Replace while preserving original case and punctuation
                enhanced_word = word.replace(clean_word, VOCABULARY_UPGRADES[clean_word])
                enhanced_words.append(enhanced_word)
            else:
                enhanced_words.append(word)
        return ' '.join(enhanced_words)
    except Exception as e:
        return f"Error in vocabulary enhancement: {str(e)}"


@tool
def tone_adjustment_tool(text: str, tone: str = "professional") -> str:
    """
    Adjusts the tone of the text for different contexts.

    Args:
        text: The text to adjust
        tone: The desired tone (formal, casual, professional, friendly)

    Returns:
        str: The text with adjusted tone
    """
    try:
        if tone not in TONE_PATTERNS:
            tone = "professional"

        result = text
        replacements = TONE_PATTERNS[tone]['replacements']

        for pattern, replacement in replacements.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        return result.strip()
    except Exception as e:
        return f"Error in tone adjustment: {str(e)}"


@tool
def text_analysis_tool(text: str) -> Dict:
    """
    Analyzes text to determine what improvements are needed.

    Args:
        text: The text to analyze

    Returns:
        Dict: Analysis results with recommendations
    """
    try:
        # Simple analysis logic
        analysis = {
            "grammar": {"issues_found": _count_grammar_issues(text)},
            "sentence": {"complex_sentences": _count_complex_sentences(text)},
            "vocabulary": {"basic_words": _count_basic_words(text)},
            "tone": {"current_tone": "neutral"}
        }

        # Determine recommended tools based on analysis
        recommended_tools = []

        # Check for grammar issues (high priority)
        if _has_grammar_issues(text):
            recommended_tools.append("grammar_correction_tool")

        # Check for complex sentences (medium priority)
        if _has_complex_sentences(text):
            recommended_tools.append("sentence_rewriting_tool")

        # Check for basic vocabulary (medium priority)
        if _has_basic_vocabulary(text):
            recommended_tools.append("vocabulary_enhancement_tool")

        # Tone adjustment is always available (low priority)
        recommended_tools.append("tone_adjustment_tool")

        return {
            "analysis": analysis,
            "recommended_tools": recommended_tools,
            "priority_order": recommended_tools,
            "text_length": len(text),
            "word_count": len(text.split())
        }
    except Exception as e:
        return {"error": f"Error in text analysis: {str(e)}"}


def _has_grammar_issues(text: str) -> bool:
    """Simple heuristic to detect potential grammar issues."""
    patterns = [
        r'\b(their|there|they\'re)\b',  # Common confusions
        r'\b(your|you\'re)\b',
        r'\b(its|it\'s)\b',
        r'[.!?]\s*[a-z]',  # Sentences not starting with capital
        r'\s{2,}',  # Multiple spaces
    ]

    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def _has_complex_sentences(text: str) -> bool:
    """Detect overly complex sentences."""
    sentences = re.split(r'[.!?]+', text)
    for sentence in sentences:
        words = sentence.split()
        if len(words) > 25:  # Long sentences
            return True
        if sentence.count(',') > 3:  # Many clauses
            return True
    return False


def _has_basic_vocabulary(text: str) -> bool:
    """Detect basic vocabulary that could be enhanced."""
    words = re.findall(r'\b\w+\b', text.lower())
    basic_count = sum(1 for word in words if word in VOCABULARY_UPGRADES)
    return basic_count > len(words) * 0.1  # More than 10% basic words


def _count_grammar_issues(text: str) -> int:
    """Count the number of grammar issues in text."""
    count = 0
    for pattern in GRAMMAR_PATTERNS:
        if not callable(GRAMMAR_PATTERNS[pattern]):
            count += len(re.findall(pattern, text, re.IGNORECASE))
    return count


def _count_complex_sentences(text: str) -> int:
    """Count the number of complex sentences."""
    sentences = re.split(r'[.!?]+', text)
    complex_count = 0
    for sentence in sentences:
        words = sentence.split()
        if len(words) > 25 or sentence.count(',') > 3:
            complex_count += 1
    return complex_count


def _count_basic_words(text: str) -> int:
    """Count the number of basic words that could be enhanced."""
    words = re.findall(r'\b\w+\b', text.lower())
    return sum(1 for word in words if word in VOCABULARY_UPGRADES)


# List of all available tools for easy access
WRITING_TOOLS = [
    grammar_correction_tool,
    sentence_rewriting_tool,
    vocabulary_enhancement_tool,
    tone_adjustment_tool,
    text_analysis_tool
]