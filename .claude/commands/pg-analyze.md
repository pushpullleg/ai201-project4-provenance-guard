# pg-analyze

Run the full Provenance Guard 2-signal detection pipeline on a piece of text and display all scored outputs.

**Text to analyze:** $ARGUMENTS

## Steps

1. Confirm the Flask app is running. Quick check:
   ```bash
   curl -s http://localhost:5001/log > /dev/null && echo "App is running" || echo "App is NOT running — start with: python3 app.py"
   ```
   If the app is not running, start it in the background: `python3 app.py &` then wait 2 seconds.

2. Submit the text to POST /submit:
   ```bash
   curl -s -X POST http://localhost:5001/submit \
     -H "Content-Type: application/json" \
     -d '{"text": "$ARGUMENTS", "creator_id": "pg-analyze-test"}' | python3 -m json.tool
   ```

3. Display and interpret the results clearly:
   - **groq_score** — what the LLM signal detected (semantic patterns)
   - **stylometric_score** — what the structural heuristics detected
   - **confidence** — combined weighted score (0.6×groq + 0.4×stylo)
   - **attribution** — which tier this falls into
   - **label** — the exact transparency label text returned
   - **content_id** — save this if you want to test an appeal

4. Interpret the signal agreement:
   - If both signals agree (both high or both low): high confidence result, explain why
   - If signals disagree significantly (>0.3 gap): explain what each signal is picking up
     and why they might diverge for this particular text

5. State which label tier was triggered and what confidence threshold boundary was crossed,
   referencing the thresholds in CLAUDE.md:
   - `> 0.75` → likely_ai
   - `0.40–0.75` → uncertain  
   - `< 0.40` → likely_human
