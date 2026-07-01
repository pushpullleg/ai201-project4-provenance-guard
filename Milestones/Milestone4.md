Milestone 4: Add the Second Signal and Implement Confidence Scoring
⏰ ~2 hours

Add your second detection signal and implement real confidence scoring. This milestone is where your detection pipeline becomes multi-signal. The key engineering challenge is combining two signals — each with its own output format and reliability profile — into a single, calibrated confidence score.


Use your detection signals section + uncertainty representation section + architecture diagram to prompt an AI tool. Ask it to generate: (1) the second signal function, and (2) the confidence scoring logic that combines both signals according to your spec. Verify that the generated scoring function actually matches the thresholds you defined in your planning document — AI tools sometimes implement reasonable-looking scoring that silently diverges from your specified ranges. If it does, correct it before wiring it in.


Implement your second detection signal as a standalone function, tested independently before integration. If you're using stylometric heuristics, compute 2–3 specific metrics (e.g., sentence length variance, type-token ratio) and decide how to combine them into a single signal score. Test it on the same inputs you used for signal 1 — do the two signals agree? Disagree? Understanding where they diverge tells you something about each signal's strengths.


Implement your confidence scoring logic. Both signals now produce a score — combine them according to your planning.md spec. Your combined score should: vary meaningfully across clearly different inputs (a highly polished, uniform paragraph vs. a casual, irregular piece should produce different scores), and map to at least 3 distinct label categories (e.g., "Likely AI-generated," "Uncertain," "Likely human-written").


Test your scoring with at least 4 deliberately chosen inputs: something you're confident is AI-generated, something you're confident is human-written, and two borderline cases. Do the scores match your intuition? If not, investigate why before moving on — a miscalibrated scoring function will undermine everything built on top of it.

If you need test inputs, here's a starting set:

# Clearly AI-generated (should score high)
"Artificial intelligence represents a transformative paradigm shift in modern society. 
It is important to note that while the benefits of AI are numerous, it is equally 
essential to consider the ethical implications. Furthermore, stakeholders across 
various sectors must collaborate to ensure responsible deployment."

# Clearly human-written (should score low)
"ok so i finally tried that new ramen place downtown and honestly? 
underwhelming. the broth was fine but they put WAY too much sodium in it and 
i was thirsty for like three hours after. my friend got the spicy version and 
said it was better. probably won't go back unless someone drags me there"

# Borderline: formal human writing (may score mid-high on stylometrics)
"The relationship between monetary policy and asset price inflation has been 
extensively studied in the literature. Central banks face a fundamental tension 
between their mandate for price stability and the unintended consequences of 
prolonged low interest rates on equity and real estate valuations."

# Borderline: lightly edited AI output (should ideally score mid-range)
"I've been thinking a lot about remote work lately. There are genuine tradeoffs — 
flexibility and no commute on one side, isolation and blurred work-life boundaries 
on the other. Studies show productivity varies widely by individual and role type."
If any of these produce scores that don't match your intuition, print both signal scores separately to find which one is misbehaving.


Update your audit log to capture both signals' individual scores alongside the combined confidence score.

📍 Checkpoint

Both detection signals are running and their outputs are combined into a single confidence score. Submitting clearly AI-generated text produces a noticeably different score than clearly human-written text. The audit log now records individual signal scores and the combined result. You have tested at least 4 inputs spanning the confidence range.