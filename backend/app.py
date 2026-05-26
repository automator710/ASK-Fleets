import os

from dotenv import load_dotenv
from flask import Flask, render_template

load_dotenv()

_root = os.path.join(os.path.dirname(__file__), "..", "frontend")
app = Flask(__name__, template_folder=os.path.join(_root, "templates"), static_folder=os.path.join(_root, "static"))
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")


# ── Customer-facing pages ───────────────────────────────────────────────────

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/features")
def features():
    return render_template("features.html")


if __name__ == "__main__":
    app.run(debug=True, port=5001)
