# pg-test-labels

Test all three transparency label variants by submitting texts designed to hit each confidence tier. Verifies that the full label range is reachable.

## Steps

1. Confirm the Flask app is running:
   ```bash
   curl -s http://localhost:5001/log > /dev/null && echo "Running" || echo "Not running — start: python3 app.py"
   ```

2. Submit three texts — one per label tier. Run all three:

   **Test A — Clearly AI-generated (target: likely_ai, confidence > 0.75):**
   ```bash
   curl -s -X POST http://localhost:5001/submit \
     -H "Content-Type: application/json" \
     -d '{"text": "Artificial intelligence represents a transformative paradigm shift in modern society. It is important to note that while the benefits of AI are numerous, it is equally essential to consider the ethical implications. Furthermore, stakeholders across various sectors must collaborate to ensure responsible deployment.", "creator_id": "label-test-ai"}' | python3 -m json.tool
   ```

   **Test B — Borderline (target: uncertain, confidence 0.40–0.75):**
   ```bash
   curl -s -X POST http://localhost:5001/submit \
     -H "Content-Type: application/json" \
     -d '{"text": "I have been thinking a lot about remote work lately. There are genuine tradeoffs — flexibility and no commute on one side, isolation and blurred work-life boundaries on the other. Studies show productivity varies widely by individual and role type.", "creator_id": "label-test-borderline"}' | python3 -m json.tool
   ```

   **Test C — Clearly Human-written (target: likely_human, confidence < 0.40):**
   ```bash
   curl -s -X POST http://localhost:5001/submit \
     -H "Content-Type: application/json" \
     -d '{"text": "ok so i finally tried that new ramen place downtown and honestly? underwhelming. the broth was fine but they put WAY too much sodium in it and i was thirsty for like three hours after. my friend got the spicy version and said it was better. probably wont go back unless someone drags me there", "creator_id": "label-test-human"}' | python3 -m json.tool
   ```

3. Display a summary table:
   ```
   Test    | Expected Tier | Actual Tier   | Confidence | Label Snippet (first 60 chars)
   --------|---------------|---------------|------------|-------------------------------
   AI text | likely_ai     | <actual>      | <score>    | <first 60 chars of label>
   Border  | uncertain     | <actual>      | <score>    | <first 60 chars of label>
   Human   | likely_human  | <actual>      | <score>    | <first 60 chars of label>
   ```

4. Check:
   - Are all 3 distinct label texts returned (not the same text for all)?
   - Do the confidence scores spread across the range (not all clustered near 0.5)?
   - Is the label text plain language (no jargon)?
   
5. Flag any FAIL cases:
   - If the same label tier appears for both AI and human text → scoring is broken
   - If the label text contains "classifier", "logit", "probability", or "score" → jargon violation
   - If all three scores are within 0.1 of each other → signal calibration issue
