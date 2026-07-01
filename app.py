import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv("groq_key.env")

from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from pipeline.groq_signal import analyze as groq_analyze
from models.audit import init_db, log_submission, get_log, get_entry, update_appeal

# ---------------------------------------------------------------------------
# Optional imports — fall back to stubs if later-milestone files are absent
# ---------------------------------------------------------------------------

try:
    from pipeline.stylometric import analyze as stylo_analyze
except ImportError:
    def stylo_analyze(text):
        return 0.5  # stub until M4

try:
    from pipeline.combiner import combine_signals
except ImportError:
    def combine_signals(g, s):
        return round(0.6 * g + 0.4 * s, 6)  # inline formula

try:
    from labels import get_label
except ImportError:
    def get_label(c):
        if c > 0.75:
            return {"tier": "likely_ai", "text": "Likely AI (label pending M5)"}
        elif c >= 0.40:
            return {"tier": "uncertain", "text": "Uncertain (label pending M5)"}
        else:
            return {"tier": "likely_human", "text": "Likely human (label pending M5)"}

try:
    from models.appeal import submit_appeal
except ImportError:
    def submit_appeal(cid, reasoning):
        from models.audit import get_entry, update_appeal
        if not get_entry(cid):
            raise ValueError("not found")
        update_appeal(cid, reasoning)
        return {
            "message": "Appeal received. Your content is now under review.",
            "content_id": cid,
            "status": "under_review",
        }

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)

init_db()

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/submit", methods=["POST"])
@limiter.limit("10 per minute;100 per day")
def submit():
    data = request.get_json(force=True, silent=True) or {}

    text = data.get("text", "").strip()
    creator_id = data.get("creator_id", "").strip()

    if not text or not creator_id:
        return jsonify({"error": "Both 'text' and 'creator_id' are required."}), 400

    content_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    groq_score = groq_analyze(text)
    stylometric_score = stylo_analyze(text)
    confidence = combine_signals(groq_score, stylometric_score)
    label_info = get_label(confidence)

    log_submission(
        content_id=content_id,
        creator_id=creator_id,
        timestamp=timestamp,
        attribution=label_info["tier"],
        confidence=confidence,
        groq_score=groq_score,
        stylometric_score=stylometric_score,
        status="classified",
        appeal_reasoning=None,
    )

    return jsonify(
        {
            "content_id": content_id,
            "creator_id": creator_id,
            "attribution": label_info["tier"],
            "confidence": confidence,
            "groq_score": groq_score,
            "stylometric_score": stylometric_score,
            "label": label_info["text"],
            "status": "classified",
            "timestamp": timestamp,
        }
    ), 200


@app.route("/appeal", methods=["POST"])
def appeal():
    data = request.get_json(force=True, silent=True) or {}

    content_id = data.get("content_id", "").strip()
    creator_reasoning = data.get("creator_reasoning", "").strip()

    if not content_id or not creator_reasoning:
        return jsonify(
            {"error": "Both 'content_id' and 'creator_reasoning' are required."}
        ), 400

    try:
        result = submit_appeal(content_id, creator_reasoning)
    except ValueError:
        return jsonify({"error": f"content_id '{content_id}' not found."}), 404

    return jsonify(result), 200


@app.route("/log", methods=["GET"])
def log():
    entries = get_log()
    return jsonify({"entries": entries}), 200


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5001)
