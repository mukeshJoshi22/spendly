import os
from datetime import datetime

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import (create_user, get_db, get_user_by_email,
                         get_user_by_id, get_user_expenses, init_db, seed_db)

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

    db_user = get_user_by_id(session["user_id"])
    if not db_user:
        session.clear()
        return redirect(url_for("login"))

    expenses = get_user_expenses(session["user_id"])

    total_spent = sum(e["amount"] for e in expenses)
    transaction_count = len(expenses)

    category_totals = {}
    for e in expenses:
        category_totals[e["category"]] = category_totals.get(e["category"], 0) + e["amount"]

    top_category = max(category_totals, key=category_totals.get) if category_totals else "—"

    categories = sorted(
        [
            {
                "name": name,
                "total": round(total, 2),
                "percent": round(total / total_spent * 100) if total_spent else 0,
            }
            for name, total in category_totals.items()
        ],
        key=lambda c: c["total"],
        reverse=True,
    )

    try:
        member_since = datetime.strptime(db_user["created_at"], "%Y-%m-%d %H:%M:%S").strftime("%B %Y")
    except (ValueError, TypeError):
        member_since = "—"

    user = {
        "name": db_user["name"],
        "email": db_user["email"],
        "member_since": member_since,
    }

    stats = {
        "total_spent": round(total_spent, 2),
        "transaction_count": transaction_count,
        "top_category": top_category,
    }

    transactions = [
        {
            "date": datetime.strptime(e["date"], "%Y-%m-%d").strftime("%b %-d, %Y"),
            "description": e["description"] or "",
            "category": e["category"],
            "amount": e["amount"],
        }
        for e in expenses
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
