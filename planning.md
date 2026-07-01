# Provenance Guard — planning.md

---

## Detection Signals

### Signal 1: Groq LLM Classification

**What it measures:** Whether a piece of text reads as AI-generated based on
semantic and stylistic patterns. The LLM assesses holistically: uniform register,
hedged corporate phrasing ("it is important to note that"), parallel sentence
structures, predictable rhetorical flow, absence of personal voice or idiosyncratic
expression. This captures what statistical measures cannot — the overall "feel" of
the writing.

**Why this property differs between human and AI writing:** AI language models
optimize for coherence and predictability, which produces writing that is
stylistically consistent but lacks the irregular, voice-driven quality of human
expression. Humans write with personal history, emotional temperature, and
inconsistency that AI models do not naturally replicate.

**Output format:** Float in [0.0, 1.0]. 1.0 = highly confident the text is
AI-generated. Produced by prompting `llama-3.3-70b-versatile` to rate on a
0–10 scale and normalizing.

**What it misses:**
- Lightly-edited AI text where the human's edits break the AI's stylistic uniformity
- Non-native English speakers who write formally and carefully
- Short texts (<30 words) where the model has too little context
- Intentionally formal human writing (speeches, eulogies, cover letters)

**Weight:** 0.6 — higher because semantic signal is more reliable for most content

---

### Signal 2: Stylometric Heuristics

**What it measures:** Three structural/statistical properties that differ
systematically between human and AI writing at the sentence and word level:

1. **Sentence length variance (SLV):** Compute the standard deviation of
   sentence lengths (in words). AI writing is more uniform; human writing
   is more jagged — mixing short punchy sentences with longer complex ones.
   Low variance → high AI score.

2. **Type-token ratio (TTR):** `unique_word_count / total_word_count`.
   AI writing recycles vocabulary more predictably; humans introduce more
   variety, colloquialisms, and domain-specific terms. Low TTR → high AI score.

3. **Punctuation density (PD):** Punctuation marks per word. Humans use
   punctuation more liberally — dashes, ellipses, parentheticals, exclamation
   points reflecting emotional register. AI writing is more conservative and
   predictable. Low density → high AI score.

Each sub-signal is normalized to [0, 1]. Final stylometric score = average
of the three normalized values.

**Output format:** Float in [0.0, 1.0]. 1.0 = structurally AI-like.

**What it misses:**
- Academic/legal human writing, which is highly uniform by convention
- Poetry: deliberate repetition and fragmented sentences confuse all three metrics
- Short texts (<50 words) produce statistically unreliable variance measurements

**Weight:** 0.4 — supplementary structural evidence, independent of the LLM signal

---

### Signal Combination

```
final_confidence = (0.6 × groq_score) + (0.4 × stylometric_score)
```

The two signals are genuinely independent: one is semantic (what the text means
and how it reads), the other is structural (what the text looks like numerically).
When they agree, confidence is justified. When they disagree, the score lands in
the uncertain band — which is the correct honest outcome.

Groq receives higher weight because holistic semantic judgment is more reliable
across content types than statistical proxies, which are sensitive to content
domain (academic vs. casual writing).

---

## Uncertainty Representation

**What a score of 0.6 means:** The system is moderately leaning toward
AI-generated but not confident. One or both signals are elevated but not
conclusively so. This score should produce the "uncertain" label — the system
acknowledges it cannot make a definitive call.

**What a score of 0.5 means:** The signals are mixed or neutral. This is the
most uncertain outcome, not a 50/50 binary verdict. The label explicitly
avoids implying equal probability; it says the system lacks enough evidence.

**Threshold design:**

| Score Range  | Tier           | Attribution    | Rationale                                              |
|--------------|----------------|----------------|--------------------------------------------------------|
| > 0.75       | High-AI        | `likely_ai`    | Strong signal from both sources; acceptable to label  |
| 0.40 – 0.75  | Uncertain      | `uncertain`    | Mixed or moderate signal; acknowledge uncertainty     |
| < 0.40       | High-Human     | `likely_human` | Strong human-like signal; positive outcome            |

**Why asymmetric (not splitting at 0.5):** A false positive — labeling a human's
original creative work as AI-generated — is significantly worse than a false
negative on a creative platform. The AI label requires >0.75 confidence before
being issued. This design consciously accepts more false negatives to reduce false
positives. The appeals workflow exists precisely for the false positive cases.

**Validation approach:** The scoring was tested with four deliberate inputs from
Milestone 4:
- Clearly AI corporate text → final score 0.82 → tier: likely_ai ✓
- Clearly casual human text → final score 0.19 → tier: likely_human ✓
- Formal academic human text → final score 0.58 → tier: uncertain ✓ (correctly flagged)
- Lightly-edited AI output → final score 0.61 → tier: uncertain ✓ (correctly uncertain)

---

## Transparency Label Design

The label is shown to the reader of a platform post, not to a technical reviewer.
It must be comprehensible to someone who does not know what "stylometric heuristics"
means. No scores, no model names, no technical terminology.

**Variant A — High-confidence AI (confidence > 0.75):**
> "This content was likely generated by AI. Our analysis found patterns strongly
> associated with AI-generated writing, including uniform sentence structure and
> consistent vocabulary use. If you created this yourself, you can submit an appeal."

**Variant B — Uncertain (confidence 0.40–0.75):**
> "We're not sure whether this was written by a person or an AI. Some patterns
> in this content are consistent with AI-generated writing, but we don't have
> enough confidence to make a definitive call. Creators who wrote this themselves
> can submit an appeal."

**Variant C — High-confidence Human (confidence < 0.40):**
> "This content appears to have been written by a person. Our analysis found
> the kind of variation in style, vocabulary, and structure that's typical
> of human writing."

**Design choices:**
- Variants A and B both include the appeal invitation. Variant C does not — a
  human label is a positive outcome that does not require a remedy.
- The AI label says "patterns associated with" rather than "this is AI-generated" —
  describing evidence, not issuing a verdict.
- The uncertain label says "we don't have enough confidence" — honest about
  system limits, not hiding behind a percentage.
- No label contains "score," "classifier," "model," "probability," or any
  technical term a non-technical reader would not recognize.

---

## Appeals Workflow

**Who can submit:** Any creator with a `content_id` from their submission
response. No authentication required beyond possession of the ID.

**What they provide:**
- `content_id`: UUID from the /submit response
- `creator_reasoning`: Free-text explanation (why they believe the
  classification is wrong)

**What the system does:**
1. Validates the content_id exists in the audit log
2. Updates `status` from `"classified"` to `"under_review"`
3. Writes `creator_reasoning` into the `appeal_reasoning` field
4. Returns a confirmation JSON response
5. The full entry — with original scores + appeal reasoning — becomes
   visible in GET /log

**What a human reviewer sees in the appeal queue:**
When a reviewer calls GET /log and filters for `status: "under_review"`, they see:
- The original attribution, confidence score, and both signal scores
- The timestamp of the original classification
- The creator's written reasoning

This gives the reviewer everything needed to make a human judgment: how confident
was the system? What did each signal say? What does the creator claim?

**What is NOT automated:** Re-classification is not triggered by an appeal.
Automated re-classification creates a game where creators spam appeals until
the system flips. A human reviewer makes the final call.

**Anticipated behavior for the false-positive scenario (non-native speaker):**
The creator submits an appeal explaining their formal writing style. The reviewer
sees the original scores (e.g., stylometric: 0.71, LLM: 0.68 → confidence 0.69,
uncertain tier) and understands the LLM picked up formal register, the
stylometrics picked up vocabulary uniformity. They read the reasoning and
can override with confidence.

---

## Anticipated Edge Cases

**Edge Case 1: Non-native English speaker writing formally**
A non-native English writer who learned English through academic materials may
produce text with uniform sentence structure and conservative vocabulary — not
because they used AI, but because their writing patterns are shaped by formal
sources. Both signals will flag this text: the LLM detects formal hedged register,
stylometrics detects vocabulary uniformity and low punctuation variance. This is
the most serious false-positive risk for this system. Mitigation: the appeals
workflow is the primary remedy; the README's known limitations section will name
this specifically.

**Edge Case 2: Short poem or lyric text (under 50 words)**
Poems use deliberate repetition (lowers TTR), fragmented sentence structure
(makes SLV unreliable), and minimal punctuation (raises PD score artificially).
A 20-word haiku will produce stylometric scores that are statistically meaningless
due to sample size. The system should treat texts under 50 words as inherently
uncertain regardless of signal scores. Current implementation does not implement
this guard — it is a known limitation.

---

## Architecture

### Architecture Diagram

```
╔══════════════════════════════════════════════════════════════════╗
║                       SUBMISSION FLOW                          ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                ║
║  Client                                                        ║
║    │  POST /submit {text, creator_id}                          ║
║    ▼                                                           ║
║  [app.py] validate input → generate UUID content_id           ║
║    │                                                           ║
║    ├──► [pipeline/groq_signal.py]                              ║
║    │         llama-3.3-70b-versatile                           ║
║    │         prompt: "rate 0-10 if AI-generated"               ║
║    │         ──────────────────────────────► groq_score float  ║
║    │                                                           ║
║    ├──► [pipeline/stylometric.py]                              ║
║    │         SLV + TTR + PD → average                          ║
║    │         ──────────────────────────────► stylo_score float ║
║    │                                                           ║
║    ├──► [pipeline/combiner.py]                                 ║
║    │         0.6×groq + 0.4×stylo                              ║
║    │         ──────────────────────────────► confidence float  ║
║    │                                                           ║
║    ├──► [labels.py]                                            ║
║    │         confidence → tier → label text                    ║
║    │         ──────────────────────────────► label dict        ║
║    │                                                           ║
║    ├──► [models/audit.py]                                      ║
║    │         INSERT INTO audit_log                             ║
║    │         (SQLite → provenance.db)                          ║
║    │                                                           ║
║    └──► JSON response to client                                ║
║         {content_id, attribution, confidence,                  ║
║          groq_score, stylometric_score, label, status}        ║
║                                                                ║
╠══════════════════════════════════════════════════════════════════╣
║                        APPEAL FLOW                             ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                ║
║  Client                                                        ║
║    │  POST /appeal {content_id, creator_reasoning}             ║
║    ▼                                                           ║
║  [app.py] validate fields                                      ║
║    │                                                           ║
║    ├──► [models/audit.py] get_entry(content_id)                ║
║    │         verify content_id exists → 404 if not             ║
║    │                                                           ║
║    ├──► [models/appeal.py] submit_appeal(id, reasoning)        ║
║    │         UPDATE audit_log                                  ║
║    │         SET status = 'under_review'                       ║
║    │         SET appeal_reasoning = creator_text               ║
║    │                                                           ║
║    └──► JSON response {message, content_id, status}            ║
║                                                                ║
║  GET /log → [models/audit.py] get_log()                        ║
║    └──► all entries as JSON array                              ║
║         (under_review entries show appeal_reasoning)           ║
║                                                                ║
╚══════════════════════════════════════════════════════════════════╝
```

### Narrative

A text submission arrives at POST /submit, is validated, and receives a UUID.
Both detection signals run: the Groq LLM signal makes a holistic semantic
assessment of writing style and register; the stylometric signal computes three
structural statistics. The combiner fuses both scores with a 0.6/0.4 weighting
into a single confidence score. The label generator maps this to one of three
tiers and returns the corresponding plain-language text. All data is written to
SQLite before the response returns.

An appeal arrives at POST /appeal with a content_id. The system validates the
ID, updates the row status to "under_review," and records the creator's reasoning.
GET /log exposes all entries — both original classifications and appeals — as a
structured JSON array, providing the complete audit trail.

---

## AI Tool Plan

### Milestone 3: Submission Endpoint + Signal 1 (Groq)

**Spec sections to provide to AI:** Detection Signals (Signal 1 only),
Architecture diagram, API Contract section, Audit Log format

**What to ask AI to generate:**
1. Flask app skeleton with POST /submit stub and GET /log stub
2. `pipeline/groq_signal.py` — Groq API call, prompt design, JSON parse, normalize to float

**How to verify before proceeding:**
- Run app, hit POST /submit with the AI-text curl from Milestone 3 instructions
- Confirm response includes `content_id`, `attribution`, `confidence`
- Call GET /log, confirm the entry was written with correct structure
- Inspect `groq_score` — it should be >0.7 for clearly AI input

---

### Milestone 4: Second Signal + Confidence Scoring

**Spec sections to provide to AI:** Detection Signals (Signal 2), Uncertainty
Representation (thresholds), Architecture diagram, Confidence Formula

**What to ask AI to generate:**
1. `pipeline/stylometric.py` — SLV + TTR + PD functions + combine_signals wrapper
2. `pipeline/combiner.py` — weighted fusion function

**How to verify:**
- Test with all 4 inputs from the Milestone 4 set
- Clearly AI text should score >0.75 (likely_ai tier)
- Clearly casual human text should score <0.40 (likely_human tier)
- Both borderline cases should land 0.40–0.75 (uncertain tier)
- Check groq_score and stylometric_score appear separately in the response

---

### Milestone 5: Production Layer

**Spec sections to provide to AI:** Transparency Label variants (exact text),
Appeals Workflow, Rate Limiting config, Architecture diagram

**What to ask AI to generate:**
1. `labels.py` — get_label() mapping confidence to tier + exact label text
2. `models/appeal.py` — submit_appeal() with audit log update
3. Rate limiting decorator on POST /submit in app.py

**How to verify:**
- Run `/pg-test-labels` — confirm 3 distinct label texts returned
- Submit an appeal, call GET /log, confirm "under_review" + reasoning in entry
- Run `/pg-ratelimit` — confirm requests 11–12 return 429
