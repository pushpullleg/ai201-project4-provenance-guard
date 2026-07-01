# pg-appeal

Submit a test appeal for a classified content entry and verify the audit log updates correctly.

**Content ID to appeal:** $ARGUMENTS

## Steps

1. If no content_id was provided, first get one from the log:
   ```bash
   curl -s http://localhost:5001/log | python3 -c "
   import json, sys
   data = json.load(sys.stdin)
   entries = data.get('entries', [])
   classified = [e for e in entries if e.get('status') == 'classified']
   if classified:
       print('Use this content_id:', classified[0]['content_id'])
   else:
       print('No classified entries found — run /pg-test-labels first')
   "
   ```

2. Show the BEFORE state of the entry:
   ```bash
   curl -s http://localhost:5001/log | python3 -c "
   import json, sys
   data = json.load(sys.stdin)
   target = '$ARGUMENTS'
   entry = next((e for e in data['entries'] if e['content_id'] == target), None)
   if entry:
       print(json.dumps(entry, indent=2))
   else:
       print('Entry not found for:', target)
   "
   ```

3. Submit the appeal:
   ```bash
   curl -s -X POST http://localhost:5001/appeal \
     -H "Content-Type: application/json" \
     -d '{"content_id": "$ARGUMENTS", "creator_reasoning": "I wrote this myself from personal experience. I am a non-native English speaker and my writing style may appear more formal than typical — I learned English through academic reading, not casual conversation."}' | python3 -m json.tool
   ```

4. Verify the response shows `"status": "under_review"`.

5. Show the AFTER state from GET /log:
   ```bash
   curl -s http://localhost:5001/log | python3 -c "
   import json, sys
   data = json.load(sys.stdin)
   target = '$ARGUMENTS'
   entry = next((e for e in data['entries'] if e['content_id'] == target), None)
   if entry:
       print(json.dumps(entry, indent=2))
   "
   ```

6. Confirm:
   - `status` changed from `"classified"` → `"under_review"`
   - `appeal_reasoning` is populated with the creator's text
   - Original `attribution`, `confidence`, `groq_score`, `stylometric_score` are unchanged
   - This entry is now the evidence for the rubric: "at least one appeal visible in the log"
