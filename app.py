import uuid
from flask import Flask, request, redirect, url_for, abort, render_template_string

from pipeline import generate_report_and_oped
from storage import load_html

app = Flask(__name__)

HOME_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>AI Research Agent</title>
  <style>
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #0f172a;
      color: #e5e7eb;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      margin: 0;
    }
    .card {
      background: #020617;
      padding: 32px;
      border-radius: 16px;
      box-shadow: 0 20px 45px rgba(0,0,0,0.7);
      max-width: 520px;
      width: 100%;
    }
    h1 {
      margin-top: 0;
      margin-bottom: 0.5rem;
      font-size: 1.6rem;
    }
    p {
      margin-top: 0;
      margin-bottom: 1.5rem;
      color: #9ca3af;
    }
    label {
      font-size: 0.9rem;
      color: #cbd5f5;
      display: block;
      margin-bottom: 0.4rem;
    }
    textarea {
      width: 100%;
      min-height: 120px;
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
    }
    button:disabled {
      opacity: 0.7;
      cursor: wait;
    }
    .footer {
      margin-top: 1.5rem;
      font-size: 0.8rem;
      color: #6b7280;
      text-align: center;
    }
  </style>
</head>
<body>
  <div class="card">
    <h1>AI Research Agent</h1>
    <p>Enter a topic and I’ll generate a research report and a matching op-ed.</p>
    <form id="topic-form" method="post" action="{{ url_for('generate') }}">
      <label for="topic">Topic</label>
      <textarea id="topic" name="topic" placeholder="e.g. Long-term impacts of AI on knowledge work" required></textarea>
      <button id="submit-btn" type="submit">Generate report &amp; op-ed</button>
    </form>
    <div class="footer">
      Private instance – behind Nginx basic auth.
    </div>
    <script>
      const form = document.getElementById('topic-form');
      const btn = document.getElementById('submit-btn');
      form.addEventListener('submit', () => {
        btn.textContent = 'Working… this may take a while';
        btn.disabled = true;
      });
    </script>
  </div>
</body>
</html>
"""

ERROR_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Error</title>
</head>
<body>
  <h1>Error</h1>
  <p>{{ message }}</p>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def index():
    return render_template_string(HOME_TEMPLATE)


@app.route("/generate", methods=["POST"])
def generate():
    topic = (request.form.get("topic") or "").strip()
    if not topic:
        return render_template_string(ERROR_TEMPLATE, message="Please provide a topic."), 400

    session_id = uuid.uuid4().hex

    try:
        generate_report_and_oped(topic, session_id)
    except Exception as e:  # log this in real usage
        return render_template_string(ERROR_TEMPLATE, message=f"Generation failed: {e}"), 500

    # After successful generation, redirect to report. Op-ed is linked from there.
    return redirect(url_for("view_report", session_id=session_id))


@app.route("/report/<session_id>")
def view_report(session_id):
    html = load_html(session_id, "report")
    if html is None:
        abort(404)
    # we stored full HTML document
    return html


@app.route("/oped/<session_id>")
def view_oped(session_id):
    html = load_html(session_id, "oped")
    if html is None:
        abort(404)
    return html
