"""
pipeline/stylometric.py — Signal 2: Stylometric Heuristics

Three sub-signals measuring structural/statistical properties that differ
between human and AI writing. Each returns a float in [0.0, 1.0] where
1.0 = more AI-like.

Final score = average of the three normalized sub-signals.
"""

import re
import math


def _sentence_length_variance(text: str) -> float:
    """
    Sub-signal 1: Sentence Length Variance (SLV).

    AI writing has MORE UNIFORM sentence lengths → LOW std dev → HIGH AI score.
    Human writing mixes short punchy sentences with long complex ones.

    Normalize: std_dev typically 0–12+ for human text; invert so low = AI.
    slv_score = 1.0 - min(std_dev / 12.0, 1.0)

    Edge case: fewer than 2 sentences → return 0.5 (insufficient signal).
    """
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if len(sentences) < 2:
        return 0.5

    word_counts = [len(re.findall(r'\b\w+\b', s)) for s in sentences]
    word_counts = [wc for wc in word_counts if wc > 0]

    if len(word_counts) < 2:
        return 0.5

    mean = sum(word_counts) / len(word_counts)
    variance = sum((wc - mean) ** 2 for wc in word_counts) / len(word_counts)
    std_dev = math.sqrt(variance)

    return 1.0 - min(std_dev / 12.0, 1.0)


def _type_token_ratio(text: str) -> float:
    """
    Sub-signal 2: Type-Token Ratio (TTR).

    TTR = unique_words / total_words.
    AI writing recycles vocabulary (low TTR) → HIGH AI score.
    Human writing introduces more variety, colloquialisms, domain terms.

    Typical range: AI ~0.40–0.60, human ~0.60–0.90.
    ttr_score = max(0.0, min(1.0, (0.90 - ttr) / 0.50))

    Edge case: fewer than 10 words → return 0.5 (insufficient signal).
    """
    words = re.findall(r'\b\w+\b', text.lower())

    if len(words) < 10:
        return 0.5

    ttr = len(set(words)) / len(words)
    return max(0.0, min(1.0, (0.90 - ttr) / 0.50))


def _punctuation_density(text: str) -> float:
    """
    Sub-signal 3: Punctuation Density (PD).

    AI writing uses punctuation conservatively (commas, periods for grammar).
    Humans use expressive punctuation: !, ?, em-dashes, ellipses, parentheses,
    semicolons, colons — marks reflecting emotional register and personal voice.

    We measure EXPRESSIVE punctuation only (excluding grammatical periods and
    commas which appear in both styles), so low expressive density → AI.

    density = expressive_punct_count / word_count
    pd_score = max(0.0, min(1.0, 1.0 - (density / 0.30)))

    Edge case: no words → return 0.5.

    Note: Using expressive-only punctuation (not all [^\\w\\s]) is the correct
    normalization because the theoretical basis is expressive register, not
    total punctuation count.  Plain periods/commas appear equally in formal AI
    output and formal human output and add no discriminative signal.
    """
    words = re.findall(r'\b\w+\b', text)

    if not words:
        return 0.5

    # Expressive / informal punctuation only — excludes "." and ","
    expressive_punct = re.findall(r'[!?;:\(\)\[\]\{\}—\-…]', text)
    density = len(expressive_punct) / len(words)
    return max(0.0, min(1.0, 1.0 - (density / 0.30)))


def analyze(text: str) -> float:
    """Combine 3 stylometric sub-signals. Returns 0.0–1.0 where 1.0 = AI-like."""
    slv = _sentence_length_variance(text)
    ttr = _type_token_ratio(text)
    pd  = _punctuation_density(text)
    return round((slv + ttr + pd) / 3.0, 6)
