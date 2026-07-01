Milestone 5: Implement the Production Layer
⏰ ~2–3 hours

Add the four production features that turn your detection pipeline into a real system: the transparency label, the appeals workflow, rate limiting, and a complete audit log. These features are independent enough to build in any order — but the transparency label and appeals workflow both depend on the confidence scoring from Milestone 4, so verify that first.


Use your transparency label variants and appeals workflow sections from planning.md + the architecture diagram to prompt an AI tool. Ask it to generate: (1) a label generation function that maps confidence scores to the correct label text, and (2) the POST /appeal endpoint. Verify the label function against your spec's thresholds — ask it to produce all three variants and confirm the text matches what you wrote. For the appeal endpoint, check that it updates status and logs correctly before considering it done.


Transparency label: Implement the three label variants you designed in planning.md. The label returned by the submission endpoint must change based on the confidence score — it should not be the same text regardless of score. Test that all three variants are reachable by submitting inputs that produce different confidence levels.


Appeals workflow: Build a POST /appeal endpoint that accepts a content_id and creator_reasoning field. The endpoint should: update the content's status to "under review" in whatever storage you're using, log the appeal alongside the original classification decision in the audit log, and return a confirmation that the appeal was received. You do not need to implement automated re-classification.

To test, use the content_id from any earlier /submit response:

curl -s -X POST http://localhost:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "PASTE-CONTENT-ID-HERE", "creator_reasoning": "I wrote this myself from personal experience. I am a non-native English speaker and my writing style may appear more formal than typical."}' | python -m json.tool
Then verify the appeal is in the log with GET /log — the entry should show "status": "under_review" and the appeal_reasoning field populated.


Rate limiting: Apply Flask-Limiter to your submission endpoint. Choose limits that reflect realistic usage (a writer submitting their own work) while preventing abuse (a script flooding the system). Document your chosen limits and reasoning in your README — the numbers should be defensible, not arbitrary.

⚙️ Flask-Limiter setup note: Flask-Limiter ≥ 3.x requires a storage_uri parameter. The simplest setup for local development uses in-memory storage:
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)
Apply the limit to your submit route:

@app.route("/submit", methods=["POST"])
@limiter.limit("10 per minute;100 per day")
def submit():
    ...
Without storage_uri="memory://" you may see a warning or error on startup.

To test that rate limiting is working, run this in a new terminal window while your Flask server is running (it sends 12 rapid requests — more than the 10/minute limit):

for i in $(seq 1 12); do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:5000/submit \
    -H "Content-Type: application/json" \
    -d '{"text": "This is a test submission for rate limit testing purposes only.", "creator_id": "ratelimit-test"}'
done
You should see 200 responses for the first 10 and 429 responses after. Capture those 429 responses in your README (paste the status-code output) — that's the evidence graders need.


Complete audit log: Verify that your log now captures everything required: timestamp, content ID, attribution result, confidence score, both individual signal scores, and whether an appeal has been filed. Check that the format is structured — JSON or a formatted log file, not unformatted console output. Generate at least 3 entries so you have something to document in your README.

📍 Checkpoint

All four production features are working: the transparency label varies by confidence level, appeals can be submitted and are reflected in the audit log, rate limiting triggers when the limit is exceeded, and the audit log has at least 3 structured entries covering submissions and at least one appeal. All of these work end-to-end without workarounds.