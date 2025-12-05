import uuid
import json
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

from flask import (
    Flask,
    request,
    jsonify,
    abort,
    render_template_string,
    url_for,
)

# Load environment variables from .env file
load_dotenv()

from pipeline import generate_full_report, HISTORY_DIR

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent


def load_history_items() -> List[Dict[str, Any]]:
    HISTORY_DIR.mkdir(exist_ok=True)
    items: List[Dict[str, Any]] = []

    for meta_path in HISTORY_DIR.glob("*.json"):
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
            items.append(data)
        except Exception:
            continue

    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return items


HOME_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>AI Research Agent</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #0f172a;
      color: #e5e7eb;
      margin: 0;
      min-height: 100vh;
      display: flex;
      justify-content: center;
      padding: 2rem 1rem 3rem;
    }
    .layout {
      width: 100%;
      max-width: 1100px;
      display: grid;
      grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr);
      gap: 2rem;
    }
    .card {
      background: #020617;
      padding: 24px 24px 28px;
      border-radius: 18px;
      box-shadow: 0 20px 45px rgba(0,0,0,0.7);
    }
    h1 {
      margin-top: 0;
      margin-bottom: 0.5rem;
      font-size: 1.6rem;
    }
    p.lead {
      margin-top: 0;
      margin-bottom: 1.5rem;
      color: #9ca3af;
      font-size: 0.95rem;
    }
    label {
      font-size: 0.9rem;
      color: #cbd5f5;
      display: block;
      margin-bottom: 0.4rem;
    }
    textarea {
      width: 100%;
      min-height: 130px;
      border-radius: 10px;
      border: 1px solid #1f2937;
      background: #020617;
      color: #e5e7eb;
      padding: 0.75rem;
      resize: vertical;
      font-family: inherit;
      font-size: 0.95rem;
    }
    button {
      margin-top: 1.2rem;
      width: 100%;
      padding: 0.8rem 1rem;
      border-radius: 999px;
      border: none;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      background: linear-gradient(135deg, #38bdf8, #6366f1);
      color: #0b1120;
      transition: transform 0.08s ease, box-shadow 0.08s ease, opacity 0.1s;
      box-shadow: 0 10px 30px rgba(37,99,235,0.45);
    }
    button:disabled {
      opacity: 0.6;
      cursor: wait;
      box-shadow: none;
    }
    .progress-container {
      margin-top: 1.2rem;
      display: none;
      flex-direction: column;
      gap: 0.4rem;
    }
    .progress-label {
      font-size: 0.8rem;
      color: #9ca3af;
    }
    .progress-bar-outer {
      width: 100%;
      height: 6px;
      border-radius: 999px;
      background: #020617;
      overflow: hidden;
      border: 1px solid #1f2937;
    }
    .progress-bar-inner {
      width: 0%;
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, #22c55e, #38bdf8, #6366f1);
      background-size: 200% 100%;
      animation: progress-pulse 1.2s ease-in-out infinite;
    }
    @keyframes progress-pulse {
      0% { transform: translateX(-10%); }
      50% { transform: translateX(10%); }
      100% { transform: translateX(-10%); }
    }
    .hint {
      margin-top: 0.4rem;
      font-size: 0.75rem;
      color: #6b7280;
    }
    .footer {
      margin-top: 1.5rem;
      font-size: 0.8rem;
      color: #6b7280;
      text-align: center;
    }
    h2 {
      font-size: 1.1rem;
      margin-top: 0;
      margin-bottom: 0.75rem;
    }
    .history-list {
      list-style: none;
      padding: 0;
      margin: 0;
      max-height: 420px;
      overflow-y: auto;
    }
    .history-empty {
      font-size: 0.9rem;
      color: #6b7280;
    }
    .history-item {
      padding: 0.75rem 0.25rem;
      border-bottom: 1px solid #111827;
    }
    .history-title {
      font-size: 0.9rem;
      margin: 0;
    }
    .history-title a {
      color: #e5e7eb;
      text-decoration: none;
    }
    .history-title a:hover {
      text-decoration: underline;
    }
    .history-meta {
      margin-top: 0.15rem;
      font-size: 0.75rem;
      color: #9ca3af;
    }
    .badge {
      padding: 2px 6px;
      border-radius: 999px;
      font-size: 0.7rem;
      text-transform: uppercase;
      margin-right: 6px;
    }
    .badge-research {
      background: #111827;
    }
    @media (max-width: 800px) {
      .layout {
        grid-template-columns: minmax(0,1fr);
      }
    }
  </style>
</head>
<body>
  <div class="layout">
    <div class="card">
      <h1>AI Research Agent</h1>
      <p class="lead">
        Generate a structured research article with citations and references.
      </p>
      <form id="topic-form">
        <label for="topic">Topic</label>
        <textarea id="topic" name="topic" placeholder="e.g. Long-term impacts of AI on engineering teams" required></textarea>

        <button id="submit-btn" type="submit">Generate report</button>

        <div class="progress-container" id="progress">
          <div class="progress-label" id="progress-label">Preparing research pipeline…</div>
          <div class="progress-bar-outer">
            <div class="progress-bar-inner" id="progress-bar"></div>
          </div>
          <div class="hint">This can take 30–90 seconds depending on the topic.</div>
        </div>
      </form>
      <div class="footer">
        All processing runs on this server using your OpenRouter API key.
      </div>
    </div>

    <div class="card">
      <h2>Past reports</h2>
      {% if history %}
      <ul class="history-list">
        {% for item in history %}
          <li class="history-item">
            <p class="history-title">
              <a href="{{ url_for('view_report', run_id=item['id']) }}">
                {{ item.get('refined_topic', item.get('user_topic','Untitled')) }}
              </a>
            </p>
            <div class="history-meta">
              <span class="badge badge-research">Research</span>
              {{ item.get('created_at', '') }}
            </div>
          </li>
        {% endfor %}
      </ul>
      {% else %}
      <div class="history-empty">
        No reports yet. Generate your first one using the form.
      </div>
      {% endif %}
    </div>
  </div>

  <script>
    const form = document.getElementById('topic-form');
    const btn = document.getElementById('submit-btn');
    const progress = document.getElementById('progress');
    const progressLabel = document.getElementById('progress-label');

    const stages = [
      "Refining topic and research questions…",
      "Designing section outline…",
      "Researching sections and assembling citations…",
      "Rendering final article…"
    ];
    let stageIndex = 0;
    let stageInterval = null;

    function startProgress() {
      progress.style.display = 'flex';
      stageIndex = 0;
      progressLabel.textContent = stages[stageIndex];
      stageInterval = setInterval(() => {
        stageIndex = (stageIndex + 1) % stages.length;
        progressLabel.textContent = stages[stageIndex];
      }, 4000);
    }

    function stopProgress() {
      if (stageInterval) clearInterval(stageInterval);
      progress.style.display = 'none';
    }

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const topicEl = document.getElementById('topic');
      const topic = topicEl.value.trim();
      if (!topic) return;

      btn.disabled = true;
      btn.textContent = "Working…";
      startProgress();

      try {
        const res = await fetch("{{ url_for('generate') }}", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ topic, report_type: "research" })
        });

        if (!res.ok) {
          throw new Error("Generation failed");
        }

        const data = await res.json();
        window.location.href = data.report_url;
      } catch (err) {
        alert("Something went wrong starting the research job. Check server logs.");
        console.error(err);
        stopProgress();
      } finally {
        btn.disabled = false;
        btn.textContent = "Generate report";
      }
    });
  </script>
</body>
</html>
"""


@app.get("/")
def index():
    history_items = load_history_items()
    return render_template_string(HOME_TEMPLATE, history=history_items)


@app.post("/generate")
def generate():
    data = request.get_json(silent=True) or {}
    topic = (data.get("topic") or "").strip()
    if not topic:
        return jsonify({"error": "Missing topic"}), 400

    report_type = "research"

    run_id = uuid.uuid4().hex

    try:
        result = generate_full_report(topic, run_id, report_type=report_type)
    except Exception as e:
        return jsonify({"error": f"Generation failed: {e}"}), 500

    return jsonify({
        "id": result["id"],
        "report_type": report_type,
        "report_url": f"/report/{result['id']}"
    })


@app.get("/report/<run_id>")
def view_report(run_id):
    html_path = HISTORY_DIR / f"{run_id}.html"
    meta_path = HISTORY_DIR / f"{run_id}.json"

    if not html_path.exists() or not meta_path.exists():
        abort(404)

    return html_path.read_text(encoding="utf-8")
