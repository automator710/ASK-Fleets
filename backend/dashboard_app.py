import os
import sys
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, session

load_dotenv()

_root = os.path.join(os.path.dirname(__file__), "..", "frontend")
dashboard_app = Flask(
    __name__,
    template_folder=os.path.join(_root, "templates"),
    static_folder=os.path.join(_root, "static"),
)
dashboard_app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")

sys.path.insert(0, os.path.dirname(__file__))
from authentication import auth_bp               # noqa: E402
from routes.dashboard_api import dashboard_api   # noqa: E402
dashboard_app.register_blueprint(auth_bp)
dashboard_app.register_blueprint(dashboard_api)

DASHBOARD_ROLES = {"admin", "manager"}


def dashboard_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login_page"))
        if session.get("role") not in DASHBOARD_ROLES:
            return render_template("unauthorized.html"), 403
        return f(*args, **kwargs)
    return decorated


@dashboard_app.route("/login")
def login_page():
    if "user" in session and session.get("role") in DASHBOARD_ROLES:
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@dashboard_app.route("/")
@dashboard_app.route("/dashboard")
@dashboard_required
def dashboard():
    return render_template("dashboard.html")


@dashboard_app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))


if __name__ == "__main__":
    dashboard_app.run(debug=True, port=5002)
