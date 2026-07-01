Milestone 3: Build the Submission Endpoint and First Detection Signal
⏰ ~2–3 hours

Build your Flask app, implement the submission endpoint, and get your first detection signal working end-to-end. Don't build all the features at once! Get one signal producing a result you can inspect before adding the second. A single working signal is easier to debug than two broken ones.

New to Flask? Start with the Flask Quickstart — a 20-minute primer covering a minimal POST/GET app, jsonify, Flask-Limiter setup, and a simple log helper.


Before writing any code, use your planning.md + architecture diagram to prompt an AI tool. Give it your detection signals section and the diagram and ask it to generate: (1) the Flask app skeleton with the POST /submit route stub, and (2) the first signal function. Review the output carefully — check that the function signature matches your spec's description of what the signal returns (a score? a binary flag?), and that the Flask route structure matches your API contract. Edit before using; don't paste blindly.


Set up your Flask app. Create a POST /submit endpoint that accepts a JSON body with at minimum a text field and a creator_id field. For now, have it return a hardcoded response so you can verify the route works before adding any logic.


Implement your first detection signal. If you're using Groq as your first signal, write a function that sends the text to the API with a prompt that returns a structured assessment. Test it independently before wiring it into the endpoint — call the function directly with a few test inputs and inspect the output.


Wire the first signal into the submission endpoint. The endpoint should now return a response with at least: a content_id (a unique ID for this submission), the attribution result from signal 1, a placeholder confidence score, and a placeholder label. The content_id is essential — the appeal endpoint needs it, and it should appear in your /submit response and audit log.

Test with a curl command:

curl -s -X POST http://localhost:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "The sun dipped below the horizon, painting the sky in hues of amber and rose. I sat on the porch, coffee in hand, watching the neighborhood slowly go quiet.", "creator_id": "test-user-1"}' | python -m json.tool
You should see a JSON response with content_id, attribution, confidence, and label fields. Save the content_id — you'll use it to test appeals in Milestone 5.


Set up your audit log. Before moving on, every call to the submission endpoint should write a structured entry to the log — timestamp, content ID, attribution result, signal 1 score. You'll extend the log in Milestone 4; start simple and make it structured (JSON or SQLite, not print() statements). A well-structured entry looks like this:

{
  "content_id": "3f7a2b1e-...",
  "creator_id": "test-user-1",
  "timestamp": "2025-04-01T14:32:10.123Z",
  "attribution": "likely_ai",
  "confidence": 0.78,
  "llm_score": 0.81,
  "status": "classified"
}

Add a GET /log endpoint that returns the most recent audit log entries as JSON. The project requires showing the audit log with at least 3 structured entries — without a /log endpoint (or equivalent), you'll have no clean way to surface this in your README. Keep it simple: return jsonify({"entries": get_log()}). In a real system this would require auth; here it's for documentation and grading visibility.

📍 Checkpoint

Your Flask app runs. POST /submit returns a JSON response including content_id, attribution result, and a placeholder confidence score. Each submission writes a structured entry to the audit log. GET /log returns those entries as JSON. You can inspect the log and see your test submissions.