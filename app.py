import os
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")

DASHBOARD_ROLES = {"admin", "manager"}


def dashboard_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            flash("Please sign in to continue.", "error")
            return redirect(url_for("landing"))
        if session.get("role") not in DASHBOARD_ROLES:
            return render_template("unauthorized.html"), 403
        return f(*args, **kwargs)
    return decorated


# ── Pages ──────────────────────────────────────────────────────────────────

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/features")
def features():
    return render_template("features.html")



@app.route("/dashboard")
@dashboard_required
def dashboard():
    return render_template("dashboard.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))




if __name__ == "__main__":
    app.run(debug=True, port=5001)
