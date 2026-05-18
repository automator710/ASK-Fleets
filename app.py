from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-production"

# In-memory users — replace with DB in production
USERS = {
    "admin@askfleets.com":   {"password": "fleet123",   "role": "admin",   "name": "Admin"},
    "manager@askfleets.com": {"password": "manager123", "role": "manager", "name": "Fleet Manager"},
    "customer@example.com":  {"password": "cust123",    "role": "customer","name": "John Customer"},
}

DASHBOARD_ROLES = {"admin", "manager"}


def dashboard_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            flash("Please sign in to continue.", "error")
            return redirect(url_for("login"))
        if session.get("role") not in DASHBOARD_ROLES:
            return render_template("unauthorized.html"), 403
        return f(*args, **kwargs)
    return decorated


@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/features")
def features():
    return render_template("features.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        if session.get("role") in DASHBOARD_ROLES:
            return redirect(url_for("dashboard"))
        return redirect(url_for("landing"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password are required.", "error")
            return render_template("login.html"), 400

        user = USERS.get(email)
        if user and user["password"] == password:
            session["user"] = email
            session["role"] = user["role"]
            session["name"] = user["name"]

            if user["role"] in DASHBOARD_ROLES:
                return redirect(url_for("dashboard"))
            else:
                flash("Your account does not have dashboard access.", "error")
                return render_template("login.html"), 403

        flash("Invalid credentials. Please check your email and password.", "error")
        return render_template("login.html"), 401

    return render_template("login.html")


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
