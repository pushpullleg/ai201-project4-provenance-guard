# pg-validate

Systematic rubric checkpoint sweep. Checks every graded item before final submission.
Run this after completing Milestone 6 (README). Reports PASS/FAIL for each item.

## Steps

Run the following checks in order. Report PASS or FAIL for each.

---

### 1. App starts without errors
```bash
python3 -c "
import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv('groq_key.env')
from app import app
print('PASS: app imports cleanly')
"
```

---

### 2. POST /submit returns all required fields
```bash
RESP=$(curl -s -X POST http://localhost:5001/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "Artificial intelligence enables unprecedented capabilities in data processing and pattern recognition, fundamentally transforming how organizations approach complex analytical challenges.", "creator_id": "validate-test"}')
echo $RESP | python3 -m json.tool
```
Check response contains: `content_id`, `creator_id`, `attribution`, `confidence`, `groq_score`, `stylometric_score`, `label`, `status`, `timestamp`
Save the content_id for later steps.

---

### 3. Both signal scores are present and distinct
From the response above, verify `groq_score != stylometric_score` (they measure different things — identical values suggest one signal is returning the other's value).

---

### 4. Confidence score is a weighted combination
Verify: `0.6 × groq_score + 0.4 × stylometric_score ≈ confidence` (within 0.001 rounding tolerance).

---

### 5. Label text is plain language (no jargon)
Read `labels.py` and check none of the three label strings contain:
"classifier", "logit", "probability", "model output", "score", "sigmoid", "neural"

---

### 6. All 3 label tiers are reachable
Run `/pg-test-labels` and confirm three distinct tier values appear.

---

### 7. POST /appeal works
```bash
# Use content_id from step 2
curl -s -X POST http://localhost:5001/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "PASTE_CONTENT_ID", "creator_reasoning": "I wrote this myself."}' | python3 -m json.tool
```
Check: response has `"status": "under_review"`

---

### 8. Appeal appears in GET /log
```bash
curl -s http://localhost:5001/log | python3 -m json.tool
```
Check: the appealed entry has `status: "under_review"` and `appeal_reasoning` populated.

---

### 9. Rate limit fires at request 11
Run `/pg-ratelimit` and verify requests 11–12 return 429.

---

### 10. Audit log has 3+ structured entries
Count entries from GET /log. Each must have: timestamp, content_id, attribution, confidence.

---

### 11. planning.md has all required sections
```bash
python3 -c "
content = open('planning.md').read()
sections = ['## Detection Signals', '## Uncertainty', '## Transparency Label', '## Appeals', '## Architecture', '## AI Tool Plan']
for s in sections:
    status = 'PASS' if s in content else 'FAIL'
    print(f'{status}: {s}')
"
```

---

### 12. README has all required sections
```bash
python3 -c "
content = open('README.md').read()
checks = [
    ('Architecture', 'Architecture overview'),
    ('Detection signals', 'detection signals'),
    ('Confidence scoring', 'confidence scor'),
    ('Label variants written out', 'This content was likely generated'),
    ('Rate limiting documented', 'per minute'),
    ('Known limitations', 'Known Limitations'),
    ('Spec reflection', 'Spec Reflection'),
    ('AI Usage section', 'AI Usage'),
]
for label, term in checks:
    status = 'PASS' if term.lower() in content.lower() else 'FAIL'
    print(f'{status}: {label}')
"
```

---

### Final Score
Report: `X/12 checks passing`. Flag every FAIL with what needs to be fixed.
