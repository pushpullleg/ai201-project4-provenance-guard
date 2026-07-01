"""
pipeline/combiner.py — Weighted score fusion for Provenance Guard.

Combines the Groq LLM signal (semantic holistic judgment) and the
stylometric signal (structural statistics) into a single confidence score.
"""


def combine_signals(groq_score: float, stylometric_score: float) -> float:
    """
    Weighted fusion: 0.6 × groq + 0.4 × stylometric

    Groq gets higher weight — semantic holistic judgment is more reliable
    than structural statistics across content types.

    Both inputs are clamped to [0.0, 1.0] before combination.

    Returns float in [0.0, 1.0] where 1.0 = confident AI-generated.
    """
    g = max(0.0, min(1.0, groq_score))
    s = max(0.0, min(1.0, stylometric_score))
    return round(0.6 * g + 0.4 * s, 6)
