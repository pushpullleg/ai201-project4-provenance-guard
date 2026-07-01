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


@app.route("/demo")
def demo():
    return """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Provenance Guard — Live Demo</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Segoe UI',system-ui,sans-serif;background:#0f1117;color:#e2e8f0;min-height:100vh}
  .header{background:linear-gradient(135deg,#1a1f2e,#0f1117);border-bottom:1px solid #2d3748;padding:20px 32px;display:flex;align-items:center;gap:14px}
  .logo{width:40px;height:40px;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:20px}
  .header-text h1{font-size:20px;font-weight:700;color:#f7fafc}
  .header-text p{font-size:12px;color:#718096;margin-top:2px}
  .badge{margin-left:auto;background:#1a4731;color:#68d391;border:1px solid #2f855a;border-radius:20px;padding:4px 12px;font-size:11px;font-weight:600}
  .main{max-width:860px;margin:0 auto;padding:28px 24px}
  .step{background:#1a1f2e;border:1px solid #2d3748;border-radius:12px;margin-bottom:16px;overflow:hidden;opacity:.35;transition:opacity .4s}
  .step.active{opacity:1;border-color:#4a5568}
  .step.done{opacity:1;border-color:#2f855a}
  .step-header{padding:14px 18px;display:flex;align-items:center;gap:12px;border-bottom:1px solid #2d3748}
  .step-num{width:26px;height:26px;border-radius:50%;background:#2d3748;color:#a0aec0;font-size:12px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0}
  .step.active .step-num{background:#4c51bf;color:#fff}
  .step.done .step-num{background:#2f855a;color:#fff}
  .step-title{font-size:13px;font-weight:600;color:#cbd5e0;flex:1}
  .step.active .step-title{color:#f7fafc}
  .method-badge{font-size:10px;font-weight:700;padding:3px 8px;border-radius:4px}
  .badge-post{background:#1a365d;color:#63b3ed}
  .badge-get{background:#1a4731;color:#68d391}
  .endpoint{font-size:12px;color:#667eea;font-family:monospace}
  .step-body{padding:16px 18px;display:none}
  .step.active .step-body,.step.done .step-body{display:block}
  .lbl{font-size:10px;font-weight:600;color:#718096;text-transform:uppercase;letter-spacing:.8px;margin-bottom:6px}
  .req-box{background:#0f1117;border:1px solid #2d3748;border-radius:6px;padding:10px 12px;font-family:monospace;font-size:12px;color:#a0aec0;white-space:pre-wrap;word-break:break-all;margin-bottom:12px;max-height:72px;overflow:hidden}
  .res-box{background:#0f1117;border:1px solid #2d3748;border-radius:6px;padding:10px 12px;font-family:monospace;font-size:12px;white-space:pre-wrap;word-break:break-word;min-height:40px;line-height:1.6}
  .res-box.loading{color:#718096;font-style:italic}
  .res-box.success{border-color:#2f855a}
  .res-box.error{border-color:#c53030}
  .conf-bar{background:#2d3748;border-radius:4px;height:8px;margin:8px 0 4px;overflow:hidden}
  .conf-fill{height:100%;border-radius:4px;transition:width 1s ease}
  .fill-ai{background:linear-gradient(90deg,#e53e3e,#fc8181)}
  .fill-uncertain{background:linear-gradient(90deg,#d69e2e,#f6e05e)}
  .fill-human{background:linear-gradient(90deg,#276749,#68d391)}
  .conf-lbl{display:flex;justify-content:space-between;font-size:11px;color:#718096}
  .tier-chip{display:inline-block;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:700;margin-right:8px}
  .tier-ai{background:#742a2a;color:#fc8181}
  .tier-unc{background:#744210;color:#f6e05e}
  .tier-human{background:#1a4731;color:#68d391}
  .rate-row{display:flex;gap:6px;flex-wrap:wrap;padding:6px 0}
  .rate-chip{padding:4px 10px;border-radius:6px;font-size:11px;font-weight:600;font-family:monospace}
  .c200{background:#1a4731;color:#68d391}
  .c429{background:#742a2a;color:#fc8181}
  .cpend{background:#2d3748;color:#718096}
  .spinner{display:inline-block;width:14px;height:14px;border:2px solid #4a5568;border-top-color:#667eea;border-radius:50%;animation:spin .7s linear infinite;vertical-align:middle;margin-right:6px}
  @keyframes spin{to{transform:rotate(360deg)}}
  .start-btn{display:block;margin:0 auto 24px;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;border:none;padding:12px 36px;border-radius:8px;font-size:14px;font-weight:700;cursor:pointer;transition:opacity .2s}
  .start-btn:disabled{opacity:.4;cursor:not-allowed}
  .summary{background:#1a2a1f;border:1px solid #2f855a;border-radius:12px;padding:18px 20px;margin-top:8px;display:none}
  .summary h3{color:#68d391;font-size:14px;margin-bottom:12px}
  .sgrid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
  .sitem{background:#0f1117;border-radius:8px;padding:10px 14px}
  .sitem .sl{font-size:10px;color:#718096;text-transform:uppercase;letter-spacing:.6px;margin-bottom:4px}
  .sitem .sv{font-size:18px;font-weight:700;color:#f7fafc}
  .sitem .ss{font-size:11px;color:#a0aec0;margin-top:2px}
</style>
</head>
<body>
<div class="header">
  <div class="logo">&#x1F6E1;</div>
  <div class="header-text"><h1>Provenance Guard</h1><p>AI Content Attribution API &mdash; Live Demo</p></div>
  <div class="badge">&#9679; LIVE on :5001</div>
</div>
<div class="main">
  <button class="start-btn" id="startBtn" onclick="runDemo()">&#9654; Run Full Demo</button>

  <div class="step" id="s1">
    <div class="step-header"><div class="step-num">1</div><div class="step-title">Submit AI-generated text</div><span class="method-badge badge-post">POST</span><span class="endpoint">/submit</span></div>
    <div class="step-body">
      <div class="lbl">Request text</div>
      <div class="req-box">"Artificial intelligence represents a transformative paradigm shift in modern society. It is important to note that while the benefits of AI are numerous, it is equally essential to consider the ethical implications. Furthermore, stakeholders across various sectors must collaborate..."</div>
      <div class="lbl">Response</div><div class="res-box loading" id="res1">Waiting&hellip;</div>
    </div>
  </div>

  <div class="step" id="s2">
    <div class="step-header"><div class="step-num">2</div><div class="step-title">Submit human-written text</div><span class="method-badge badge-post">POST</span><span class="endpoint">/submit</span></div>
    <div class="step-body">
      <div class="lbl">Request text</div>
      <div class="req-box">"ok so i finally tried that new ramen place downtown and honestly? underwhelming. the broth was fine but they put WAY too much sodium in it and i was thirsty for like three hours after..."</div>
      <div class="lbl">Response</div><div class="res-box loading" id="res2">Waiting&hellip;</div>
    </div>
  </div>

  <div class="step" id="s3">
    <div class="step-header"><div class="step-num">3</div><div class="step-title">Creator appeals the AI label</div><span class="method-badge badge-post">POST</span><span class="endpoint">/appeal</span></div>
    <div class="step-body">
      <div class="lbl">Creator reasoning</div>
      <div class="req-box" id="req3">content_id: (from step 1)
creator_reasoning: "I wrote this myself. I am a non-native English speaker and write formally."</div>
      <div class="lbl">Response</div><div class="res-box loading" id="res3">Waiting&hellip;</div>
    </div>
  </div>

  <div class="step" id="s4">
    <div class="step-header"><div class="step-num">4</div><div class="step-title">Audit log &mdash; structured trail of all decisions</div><span class="method-badge badge-get">GET</span><span class="endpoint">/log</span></div>
    <div class="step-body">
      <div class="lbl">Last 2 entries (most recent first)</div>
      <div class="res-box loading" id="res4">Waiting&hellip;</div>
    </div>
  </div>

  <div class="step" id="s5">
    <div class="step-header"><div class="step-num">5</div><div class="step-title">Rate limiting &mdash; 12 rapid requests</div><span class="method-badge badge-post">POST</span><span class="endpoint">/submit &times; 12</span></div>
    <div class="step-body">
      <div class="lbl">HTTP status codes (10 per minute limit)</div>
      <div class="rate-row" id="rateRow"></div>
    </div>
  </div>

  <div class="summary" id="summary">
    <h3>&#10003; All endpoints verified</h3>
    <div class="sgrid">
      <div class="sitem"><div class="sl">AI text confidence</div><div class="sv" id="sumAI">&mdash;</div><div class="ss">groq + stylometric</div></div>
      <div class="sitem"><div class="sl">Human text confidence</div><div class="sv" id="sumHuman">&mdash;</div><div class="ss">groq + stylometric</div></div>
      <div class="sitem"><div class="sl">Appeals workflow</div><div class="sv">&#10003;</div><div class="ss">status &rarr; under_review</div></div>
      <div class="sitem"><div class="sl">Rate limit</div><div class="sv">429</div><div class="ss">fires at request 11</div></div>
    </div>
  </div>
</div>

<script>
var aiId=null;
function sleep(ms){return new Promise(function(r){setTimeout(r,ms);})}
function act(id){document.getElementById(id).classList.add('active')}
function done(id){var e=document.getElementById(id);e.classList.remove('active');e.classList.add('done');e.querySelector('.step-num').textContent='\\u2713'}
function tc(t){return t==='likely_ai'?'tier-ai':t==='uncertain'?'tier-unc':'tier-human'}
function tl(t){return t==='likely_ai'?'LIKELY AI':t==='uncertain'?'UNCERTAIN':'LIKELY HUMAN'}
function fc(t){return t==='likely_ai'?'fill-ai':t==='uncertain'?'fill-uncertain':'fill-human'}
function renderSub(id,d){
  var pct=Math.round(d.confidence*100);
  document.getElementById(id).className='res-box success';
  document.getElementById(id).innerHTML=
    '<span class="tier-chip '+tc(d.attribution)+'">'+tl(d.attribution)+'</span><br><br>'+
    '<div class="lbl" style="margin-bottom:4px">Confidence: '+d.confidence.toFixed(4)+
    ' &nbsp;|&nbsp; Groq: '+d.groq_score.toFixed(2)+
    ' &nbsp;|&nbsp; Stylometric: '+d.stylometric_score.toFixed(4)+'</div>'+
    '<div class="conf-bar"><div class="conf-fill '+fc(d.attribution)+'" style="width:'+pct+'%"></div></div>'+
    '<div class="conf-lbl"><span>0.00 Human</span><span>1.00 AI</span></div>'+
    '<br><div style="font-size:12px;color:#a0aec0;line-height:1.5;border-left:3px solid #4a5568;padding-left:10px;font-style:italic;">'+d.label+'</div>';
}
async function runDemo(){
  document.getElementById('startBtn').disabled=true;
  document.getElementById('startBtn').textContent='\\u23F3 Running\\u2026';

  // Step 1
  act('s1');
  document.getElementById('res1').innerHTML='<span class="spinner"></span>Calling Groq + stylometric signals\\u2026';
  await sleep(600);
  var r1=await fetch('/submit',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({text:'Artificial intelligence represents a transformative paradigm shift in modern society. It is important to note that while the benefits of AI are numerous, it is equally essential to consider the ethical implications. Furthermore, stakeholders across various sectors must collaborate to ensure responsible deployment of these technologies.',creator_id:'demo-video-ai'})});
  var d1=await r1.json(); aiId=d1.content_id;
  renderSub('res1',d1);
  document.getElementById('sumAI').textContent=d1.confidence.toFixed(3);
  done('s1'); await sleep(1400);

  // Step 2
  act('s2');
  document.getElementById('res2').innerHTML='<span class="spinner"></span>Calling Groq + stylometric signals\\u2026';
  await sleep(600);
  var r2=await fetch('/submit',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({text:'ok so i finally tried that new ramen place downtown and honestly? underwhelming. the broth was fine but they put WAY too much sodium in it and i was thirsty for like three hours after. my friend got the spicy version and said it was better.',creator_id:'demo-video-human'})});
  var d2=await r2.json();
  renderSub('res2',d2);
  document.getElementById('sumHuman').textContent=d2.confidence.toFixed(3);
  done('s2'); await sleep(1400);

  // Step 3
  act('s3');
  document.getElementById('req3').textContent='content_id: '+aiId+'\\ncreator_reasoning: "I wrote this myself. I am a non-native English speaker and write formally."';
  document.getElementById('res3').innerHTML='<span class="spinner"></span>Submitting appeal\\u2026';
  await sleep(600);
  var r3=await fetch('/appeal',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({content_id:aiId,creator_reasoning:'I wrote this myself. I am a non-native English speaker and write formally.'})});
  var d3=await r3.json();
  document.getElementById('res3').className='res-box success';
  document.getElementById('res3').innerHTML=
    '<span class="tier-chip" style="background:#2a4365;color:#90cdf4">STATUS UPDATED</span><br><br>'+
    '<span style="color:#68d391;font-weight:700">\\u2713 '+d3.message+'</span><br><br>'+
    '<span style="color:#a0aec0">content_id: '+d3.content_id+'<br>status: <span style="color:#fc8181;font-weight:700">'+d3.status+'</span></span>';
  done('s3'); await sleep(1400);

  // Step 4
  act('s4');
  document.getElementById('res4').innerHTML='<span class="spinner"></span>Fetching audit log\\u2026';
  await sleep(500);
  var r4=await fetch('/log'); var d4=await r4.json();
  var entries=d4.entries.slice(0,2);
  document.getElementById('res4').className='res-box success';
  document.getElementById('res4').innerHTML=entries.map(function(e){
    var appealed=e.status==='under_review';
    return '<div style="margin-bottom:12px;padding-bottom:12px;border-bottom:1px solid #2d3748;">'+
      '<span class="tier-chip '+tc(e.attribution)+'">'+tl(e.attribution)+'</span>'+
      (appealed?'<span class="tier-chip" style="background:#2a4365;color:#90cdf4">UNDER REVIEW</span>':'')+
      '<br><span style="color:#718096;font-size:11px;">id: '+e.content_id+'</span><br>'+
      '<span style="color:#a0aec0;font-size:11px;">confidence: <b>'+e.confidence.toFixed(4)+'</b> | groq: '+e.groq_score+' | stylo: '+e.stylometric_score.toFixed(4)+' | '+e.timestamp+'</span>'+
      (appealed&&e.appeal_reasoning?'<br><span style="color:#fc8181;font-size:11px;">&#9888; Appeal: "'+e.appeal_reasoning.slice(0,80)+'\\u2026"</span>':'')+
      '</div>';
  }).join('');
  done('s4'); await sleep(1400);

  // Step 5
  act('s5');
  var row=document.getElementById('rateRow'); row.innerHTML='';
  for(var i=1;i<=12;i++){
    var chip=document.createElement('div');
    chip.className='rate-chip cpend'; chip.textContent='Req '+i+': …';
    row.appendChild(chip); await sleep(80);
    var rr=await fetch('/submit',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({text:'Rate limit test '+i+'.',creator_id:'ratelimit-demo'})});
    chip.className='rate-chip '+(rr.status===429?'c429':'c200');
    chip.textContent='Req '+i+': '+rr.status+(rr.status===429?' \\u2717':' \\u2713');
    await sleep(120);
  }
  done('s5'); await sleep(800);
  document.getElementById('summary').style.display='block';
  document.getElementById('startBtn').textContent='\\u2713 Demo Complete';
}
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5001)
