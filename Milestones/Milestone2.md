Milestone 2: Write Your Spec Before Any Code
⏰ ~1–2 hours

Write your planning.md before any implementation. There is no template — design the document structure yourself. What matters is that you address the five questions below with real, specific answers. A vague answer to "how will you represent uncertainty?" will produce a vague implementation, and you won't discover that until you're trying to explain a 0.62 confidence score to a non-technical user.

This document is also your primary AI prompting tool. When you reach Milestones 3–5, you'll give sections of this spec — plus the architecture diagram — to an AI tool to generate implementation code. A vague spec produces vague code. A spec that answers "what does signal 1's output look like?" and "what thresholds separate my three label variants?" gives AI tools something concrete to implement against.


Create planning.md in your repo root. Design the structure yourself. At minimum, your document must address these five questions with specific, implementation-ready answers:

Detection signals: What are your 2+ signals? What does each one measure? What does each signal's output look like (a score between 0–1? a binary flag?), and how will you combine them into a single confidence score?
Uncertainty representation: What does a confidence score of 0.6 mean to your system? How will you map raw signal outputs to a calibrated score? What threshold separates "likely AI" from "uncertain" from "likely human"?
Transparency label design: What exact text will the label show for a high-confidence AI result? A high-confidence human result? An uncertain result? Write out the three label variants now, before you build the UI.
Appeals workflow: Who can submit an appeal? What information do they provide? What does the system do when an appeal is received — what status changes, what gets logged? What would a human reviewer see when they open the appeal queue?
Anticipated edge cases: What types of content will your system handle poorly? Name at least two specific scenarios — not generic risks like "inaccurate detection," but specific cases like "a poem with heavy use of repetition and simple vocabulary that your heuristics might score as AI-generated."

Add an ## Architecture section to your planning.md. Include the diagram you drew in Milestone 1 (ASCII art is fine) and a 2–3 sentence narrative describing the submission and appeal flows. This section travels with you into Milestones 3–5 as the reference diagram for AI code generation.


Add an ## AI Tool Plan section to your planning.md. For each of the three implementation milestones, specify:

M3 (submission endpoint + first signal): Which spec sections you'll provide to the AI tool (hint: your detection signals section + the diagram), what you'll ask it to generate (Flask app skeleton + the first signal function), and how you'll verify the output (test with a few inputs directly before wiring into the endpoint).
M4 (second signal + confidence scoring): Which spec sections you'll provide (detection signals + uncertainty representation + diagram), what you'll ask for (second signal function + scoring logic), and what you'll check (do scores vary meaningfully between clearly AI and clearly human text?).
M5 (production layer): Which spec sections you'll provide (label variants + appeals workflow + diagram), what you'll ask for (label generation logic + the /appeal endpoint), and how you'll verify (test all three label variants are reachable and that an appeal updates status correctly).

Review your label variants. Revise if needed before you start building.


Update planning.md before starting any stretch features.

📍 Checkpoint

planning.md addresses all five questions with specific answers. You have written out the three label variants (high-confidence AI, high-confidence human, uncertain). Your confidence scoring approach produces different labels at different score ranges — not a binary flip at 0.5. Your ## Architecture section includes the diagram from Milestone 1. Your ## AI Tool Plan section covers all three implementation milestones with specific sections, requests, and verification steps.