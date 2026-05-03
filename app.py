import os

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import create_user, get_db, get_user_by_email, init_db, seed_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()

    if not name or not email or not password:
        return render_template("register.html", error="All fields are required.", name=name, email=email, password=password)

    if len(password) < 8:
        return render_template("register.html", error="Password must be at least 8 characters.", name=name, email=email, password=password)

    if get_user_by_email(email):
        return render_template("register.html", error="An account with that email already exists.", name=name, email=email, password=password)

    password_hash = generate_password_hash(password, method="pbkdf2:sha256")
    user_id = create_user(name, email, password_hash)

    session["user_id"] = user_id
    session["user_name"] = name

    return redirect(url_for("landing"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()

    if not email or not password:
        return render_template("login.html", error="All fields are required.", email=email)

    user = get_user_by_email(email)
    if not user or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error="Invalid email or password.", email=email)

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]

    return redirect(url_for("profile"))


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user = {
        "name": "Demo User",
        "email": "demo@spendly.com",
        "member_since": "January 2025",
    }

    stats = {
        "total_spent": 336.25,
        "transaction_count": 8,
        "top_category": "Food",
    }

    transactions = [
        {"date": "May 22, 2026", "description": "Restaurant dinner",        "category": "Food",          "amount": 22.75},
        {"date": "May 18, 2026", "description": "Miscellaneous",             "category": "Other",         "amount": 10.00},
        {"date": "May 15, 2026", "description": "New shoes",                 "category": "Shopping",      "amount": 60.00},
        {"date": "May 12, 2026", "description": "Streaming subscriptions",   "category": "Entertainment", "amount": 25.00},
        {"date": "May 08, 2026", "description": "Pharmacy",                  "category": "Health",        "amount": 35.00},
    ]

    categories = [
        {"name": "Bills",         "total": 120.00, "percent": 36},
        {"name": "Shopping",      "total":  60.00, "percent": 18},
        {"name": "Transport",     "total":  45.00, "percent": 13},
        {"name": "Health",        "total":  35.00, "percent": 10},
        {"name": "Entertainment", "total":  25.00, "percent":  7},
        {"name": "Food",          "total":  41.25, "percent": 12},
        {"name": "Other",         "total":  10.00, "percent":  3},
    ]

    return render_template("profile.html", user=user, stats=stats,
                           transactions=transactions, categories=categories)


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Database bootstrap                                                  #
# ------------------------------------------------------------------ #

with app.app_context():
    init_db()
    seed_db()


if __name__ == "__main__":
    app.run(debug=True, port=5001)
