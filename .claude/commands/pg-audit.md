# pg-audit

View and validate the Provenance Guard structured audit log.

## Steps

1. Fetch the audit log:
   ```bash
   curl -s http://localhost:5001/log | python3 -m json.tool
   ```

2. Count the total entries and report:
   ```
   Total entries: N
   Classified:    X
   Under review:  Y (appealed)
   ```

3. Check every entry has ALL required fields (rubric requirement):
   - `content_id` — present and non-empty
   - `creator_id` — present
   - `timestamp` — present and in ISO-8601 format
   - `attribution` — one of: "likely_ai", "uncertain", "likely_human"
   - `confidence` — float between 0.0 and 1.0
   - `groq_score` — float between 0.0 and 1.0
   - `stylometric_score` — float between 0.0 and 1.0
   - `status` — one of: "classified", "under_review"
   - `appeal_reasoning` — present (null or string)

4. Highlight any entries where `status == "under_review"`:
   Show the content_id, attribution, confidence, and the appeal_reasoning text
   so the reviewer context is visible.

5. Rubric readiness check:
   - PASS/FAIL: At least 3 entries present
   - PASS/FAIL: At least 1 entry has status "under_review" with appeal_reasoning populated
   - PASS/FAIL: All entries have attribution + confidence + timestamp
   - PASS/FAIL: Format is structured JSON (not plain text)

6. If fewer than 3 entries exist, generate the missing ones:
   ```bash
   # Submit enough test texts to reach 3 entries
   curl -s -X POST http://localhost:5001/submit \
     -H "Content-Type: application/json" \
     -d '{"text": "The morning light filtered through the curtains. I had forgotten to set an alarm, which is very unlike me. Strange how a small disruption can throw off an entire day.", "creator_id": "audit-fill-1"}' | python3 -m json.tool
   ```
